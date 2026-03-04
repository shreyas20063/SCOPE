# Simulation Ideas from Lectures 21-25: Sampling, Quantization, Modulation, and Applications

## Simulation: Spectral Replication Visualizer

### Lecture Source: Lecture 21, Pages 2-6

### Visual Cues Observed
- Impulse train sampling diagrams showing x_p(t) = Σ x[n]δ(t - nT)
- Frequency domain replication patterns with copies of X(jω) appearing at integer multiples of ω_s
- Four progressively denser aliasing demonstrations showing how the output frequency spectrum repeats and overlaps
- Check Yourself problems asking about which harmonics appear after sampling

### Learning Objective
Enable students to visualize the dual relationship between sampling in time domain and spectral replication in frequency domain, understanding why aliasing occurs geometrically.

### Theoretical Foundation
When a signal is sampled with period T, its spectrum is replicated at intervals of ω_s = 2π/T. For a signal x[n] = x(nT), the CTFT of the sampled signal is:
X_p(jω) = (1/T) Σ_{k=-∞}^{∞} X(j(ω - kω_s))

Without anti-aliasing, overlapping replicas cause aliasing. The Nyquist criterion requires ω_s ≥ 2ω_max.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Signal Frequency | 0.1-5 kHz | Frequency component of input signal | Slider |
| Sampling Rate | 2-50 kHz | Samples per second (f_s = 1/T) | Slider |
| Signal Amplitude | 0.1-2.0 | Magnitude of test sinusoid | Slider |
| Nyquist Display | true/false | Show Nyquist frequency band (±ω_s/2) | Toggle |
| Anti-alias Filter | true/false | Apply ideal rectangular LPF | Toggle |
| Num Replicas | 1-5 | Number of spectral copies to show | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Time Domain Signal | Continuous curve with sample markers | Show original CT and DT representations |
| Spectrum X(jω) | Magnitude plot (0-f_s*3) | Display original spectrum and replicas |
| Replicas Overlay | Colored overlapping copies at ±kf_s | Illustrate spectral replication mechanism |
| Nyquist Band | Shaded region ±f_s/2 | Highlight the "safe" frequency region |
| Aliased Frequencies | Annotations showing fold-back | Quantify which frequencies alias to which |

### Visualization Strategy
- Left panel: Time domain showing x(t), sample points x[n], and reconstructed x_r(t)
- Right panel (stacked):
  - Original spectrum X(jω)
  - Replica spectrum X_p(jω) with all copies visible
  - Frequency axis marked with ±ω_s/2 boundaries (Nyquist)
  - Toggle anti-aliasing filter to show truncation of spectrum before sampling
- Interactive: Drag signal frequency slider to watch replicas shift left/right
- Highlight: When signal frequency enters aliasing region (|f| > f_s/2), annotate the alias frequency
- Animation: Show convolution of X(jω) with impulse train P(jω) = (1/T)Σδ(ω - kω_s)

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- FFT computation of sampled signal: x_p[n] produces X_p(e^{jω})
- Replica positioning: replicas centered at ω = kω_s for integer k
- Anti-aliasing: ideal LPF with cutoff at ω_s/2 (sharp rectangular filter)
- Alias frequency calculation: f_alias = |f_signal - round(f_signal / f_s) * f_s|
- Use parametric display: plot X(jω - kω_s) for k = -2, -1, 0, 1, 2

**Code Outline:**
```python
class SpectralReplicationVisualizer(BaseSimulator):
    def _compute(self):
        # Generate signal x(t)
        t = np.linspace(0, 3/self.f_signal, 1000)
        x_t = np.cos(2*np.pi*self.f_signal*t)

        # Sample signal
        t_samples = np.arange(0, 3/self.f_signal, 1/self.f_s)
        x_n = np.cos(2*np.pi*self.f_signal*t_samples)

        # Compute spectrum (using FFT)
        omega = np.linspace(-3*np.pi*self.f_s, 3*np.pi*self.f_s, 2048)
        X = self._evaluate_spectrum(omega, self.f_signal)
        X_p = (1/self.T) * sum(self._evaluate_spectrum(omega - k*self.omega_s, self.f_signal)
                               for k in range(-5, 6))

        # Apply anti-aliasing if enabled
        if self.anti_alias:
            mask = np.abs(omega) <= np.pi*self.f_s/2
            X_filtered = X.copy()
            X_filtered[~mask] = 0
            X_p = (1/self.T) * sum(self._evaluate_spectrum(omega - k*self.omega_s, ...) * mask ...)

        return {
            'time_domain': {'t': t, 'x': x_t, 't_samples': t_samples, 'x_samples': x_n},
            'frequency_domain': {'omega': omega, 'X': X, 'X_p': X_p},
            'metadata': {'f_s': self.f_s, 'nyquist': self.f_s/2, 'f_signal': self.f_signal}
        }
```

### Extension Ideas
1. **Stereoscopic Frequency Sweep**: Animate signal frequency from 0 to 2*f_s while showing replica movement in real time
2. **2D Image Sampling**: Show sampling of 2D images (e.g., checkerboard, Baboon) with tunable sampling frequency
3. **Multi-Signal Mixing**: Sample sum of two cosines; show how their replicas can overlap (aliasing in mixed signals)
4. **Alias Tone Detective**: Given a sampled signal with unknown input frequency, let student guess which replica it came from
5. **Phase Response**: Show how replica phase (currently all aligned) could shift with non-ideal reconstruction filters

---

## Simulation: Anti-Aliasing Filter Designer

### Lecture Source: Lecture 21, Pages 3-4; Lecture 22, Page 1

### Visual Cues Observed
- CT Model of Sampling and Reconstruction block diagram: x(t) → [Impulse Reconstruction] → x_p(t) → [LPF] → x_r(t)
- Anti-Aliasing Filter block diagram: x(t) → [Anti-aliasing Filter] → [Sampler] → x[n]
- Explicit frequency responses showing ideal anti-aliasing filter (sharp cutoff at ±ω_s/2)
- Check Yourself examples: "To avoid aliasing, remove frequency components..."

### Learning Objective
Allow students to design and evaluate real anti-aliasing filters, understand trade-offs between ideal brick-wall filters and practical implementations (Butterworth, Chebyshev).

### Theoretical Foundation
Ideal anti-aliasing: multiply spectrum X(jω) by ideal LPF H(jω) = rect(ω/(ω_s/2)) before sampling.
Practical filters: approximate ideal behavior using Butterworth, Chebyshev, or Elliptic designs.
Filter order trade-off: higher order → steeper roll-off but more phase distortion and delay.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Filter Type | Butterworth, Chebyshev, Elliptic, Ideal | Filter family | Select |
| Filter Order | 1-8 | Steepness of cutoff | Slider |
| Cutoff Frequency | 0.1-0.9*f_s/2 | Normalized cutoff | Slider |
| Passband Ripple (Chebyshev) | 0.1-3 dB | Ripple in passband | Slider |
| Stopband Attenuation (Elliptic) | 20-100 dB | Minimum stopband rejection | Slider |
| Input Signal Type | Sinusoid, Chirp, Multi-tone, Real Audio | Test signal | Select |
| Signal Bandwidth | 0.1-0.8*f_s | Occupied BW of input | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Magnitude Response | Bode magnitude plot | Show passband gain and stopband attenuation |
| Phase Response | Phase angle vs. frequency | Display linear phase or distortion |
| Group Delay | d(phase)/dω vs. frequency | Show dispersion/time delay across frequencies |
| Input Spectrum | Original X(jω) | Unfiltered signal spectrum |
| Filtered Spectrum | X_filtered(jω) = H(jω)·X(jω) | Post-filter spectrum ready for sampling |
| Time Domain Comparison | x(t) and x_filtered(t) | Visual waveform distortion from filtering |
| Alias Visualization | Replicas after filtering | Demonstrate suppression of aliased components |

### Visualization Strategy
- Three-panel layout:
  - Top: Magnitude response (dB) of selected filter with passband/stopband zones shaded
  - Middle: Phase response and group delay plots
  - Bottom: Time-domain before/after filter for selected test signal
- Interactive controls: adjusting Order/Ripple/Attenuation updates plots in real time
- Overlay: mark cutoff (-3dB) point, Nyquist frequency, and signal bandwidth
- Comparison mode: side-by-side magnitude responses of all filter types at same order
- Alias markers: show where aliased spectral replicas would appear after sampling

### Implementation Notes
**Complexity:** Medium to High

**Key Algorithms:**
- Butterworth poles: computed via analog prototype with normalized cutoff at ω_n = 1
- Chebyshev Type I: use SciPy `signal.butter`, `signal.cheby1` with ripple parameter
- Elliptic (Cauer): `signal.ellip` with passband ripple and stopband atten. specs
- Bilinear transform: convert continuous H(s) to digital H(z) for discrete-time realization
- Group delay: computed as -d(arg(H(jω)))/dω
- Frequency warping: pre-warp cutoff frequency for bilinear transform

**Code Outline:**
```python
class AntiAliasingFilterDesigner(BaseSimulator):
    def _compute(self):
        # Design filter in continuous time
        if self.filter_type == "Butterworth":
            b, a = signal.butter(self.order, 2*np.pi*self.fc, analog=True)
        elif self.filter_type == "Chebyshev":
            b, a = signal.cheby1(self.order, self.ripple_db, 2*np.pi*self.fc, analog=True)
        elif self.filter_type == "Elliptic":
            b, a = signal.ellip(self.order, self.ripple_db, self.atten_db,
                               2*np.pi*self.fc, analog=True)
        elif self.filter_type == "Ideal":
            # Ideal brick-wall approximation (very high-order Butterworth)
            b, a = signal.butter(12, 2*np.pi*self.fc, analog=True)

        # Compute frequency response
        w = np.logspace(-1, np.log10(self.f_s), 1024)
        w_rad = 2*np.pi*w
        w_dig, h = signal.freqs(b, a, w_rad)
        mag_db = 20*np.log10(np.abs(h) + 1e-10)
        phase = np.angle(h)

        # Group delay
        gd = -np.gradient(np.unwrap(phase), w_rad)

        # Apply to test signal
        x_filtered = self._filter_signal(x_input, b, a)

        # Compute spectra before/after
        X_before = np.fft.fft(x_input)
        X_after = np.fft.fft(x_filtered)

        return {
            'magnitude_db': {'w': w, 'mag': mag_db},
            'phase': {'w': w, 'phase': phase},
            'group_delay': {'w': w, 'gd': gd},
            'time_domain': {'t': t, 'x_before': x_input, 'x_after': x_filtered},
            'frequency_domain': {'f': freqs, 'X_before': X_before, 'X_after': X_after}
        }
```

### Extension Ideas
1. **Filter Comparison Dashboard**: Show Bode plots of all filter types on same axis with legend
2. **Step Response & Ringing**: Show filter's step response to visualize overshoot and settling time
3. **Cascade Filters**: Build multi-stage filters (e.g., 2nd + 2nd order) to approximate higher order
4. **Nyquist Plot**: Stability analysis in complex plane for custom pole/zero specifications
5. **Real Audio Anti-Aliasing**: Upload/select audio file, design filter to suppress >22 kHz content

---

## Simulation: Quantization Artifact Explorer

### Lecture Source: Lecture 22, Pages 3-7

### Visual Cues Observed
- Quantization level diagrams: Input voltage mapped to discrete output codes (2-bit, 3-bit, 4-bit, 8-bit examples)
- Quantizing Images section: Baboon image quantized to 8-bit, 7-bit, ..., 3-bit, 1-bit showing progressive quality loss
- Banding artifact examples and dithering solutions
- Roberto's method: adding small random dither noise to reduce banding
- Quantization schemes: uniform vs. non-uniform (logarithmic for audio)

### Learning Objective
Demonstrate the visual effects of amplitude quantization, trade-offs between bit depth and image quality, and the benefits of dithering in reducing banding artifacts.

### Theoretical Foundation
Quantization: x_q[n] = Q(x[n]) where Q rounds continuous amplitude to nearest level.
Uniform quantization: levels spaced Δ apart. Quantization error: |e[n]| ≤ Δ/2.
Banding: visible contours in smooth gradients when bit depth is insufficient.
Dithering: adding small random noise before quantization spreads quantization error, reducing visual banding at cost of increased noise floor.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Bit Depth | 1-8 | Number of quantization levels = 2^bit_depth | Slider |
| Quantization Type | Uniform, Logarithmic, Weighted | Mapping scheme | Select |
| Dither Type | None, White, Triangular, Shaped | Dither noise for banding reduction | Select |
| Dither Amplitude | 0-1 LSB | Strength of dither noise | Slider |
| Input Image | Gradient, Baboon, Sunset, Synthetic | Test image for demonstration | Select |
| Artifact Focus | Banding, Noise, Blur | Which artifact to highlight | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Quantized Image | 2D image display | Show quantized output |
| Error Map | Difference image (original - quantized) | Visualize quantization error spatial distribution |
| Histogram | Amplitude distribution of input/output | Show clustering of values at quantization levels |
| Banding Contours | 3D surface plot or false-color overlay | Highlight visible contours from coarse quantization |
| Noise Power Spectrum | Spectral density of quantization noise | Show noise characteristics with/without dithering |
| Numerical Metrics | PSNR, SSIM, subjective quality score | Quantify image quality degradation |

### Visualization Strategy
- Three-column layout:
  - Left: Original image
  - Middle: Quantized image with adjustable bit depth
  - Right: Error magnitude or banding visualization
- Toggles:
  - Dither on/off to show impact on artifact reduction
  - Histogram overlay on left image showing how many levels are occupied
  - False-color "banding map" highlighting contours
- Slider: real-time adjustment of bit depth; smooth transition between 1-8 bits
- Zoom: allow magnified view of transition regions to see dithering texture
- Comparison: before/after split-screen with slider control

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- Uniform quantization: x_q = round(x / Δ) * Δ where Δ = (x_max - x_min) / (2^b - 1)
- Logarithmic quantization: used in audio (µ-law, A-law companding)
- Dithering: x_dithered = x + dither_noise before quantization
- Banding detection: compute local gradient magnitude; highlight regions with gradient < threshold
- Perceptual weighting: weight quantization error by human visual sensitivity (e.g., CSF-based)

**Code Outline:**
```python
class QuantizationArtifactExplorer(BaseSimulator):
    def _compute(self):
        # Load/generate image
        img = self._load_image(self.image_type)  # Normalized to [0, 1]

        # Add dither if enabled
        if self.dither_type != "None":
            dither = self._generate_dither(img.shape, self.dither_type, self.dither_amplitude)
            img_dithered = np.clip(img + dither, 0, 1)
        else:
            img_dithered = img

        # Quantize
        levels = 2**self.bit_depth
        img_quantized = np.round(img_dithered * (levels - 1)) / (levels - 1)

        # Compute error
        error = np.abs(img - img_quantized)

        # Banding detection
        grad_x = np.abs(np.gradient(img_quantized, axis=1))
        grad_y = np.abs(np.gradient(img_quantized, axis=0))
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        banding_map = (grad_mag < 0.01).astype(float)  # Low gradient = potential banding

        # Compute metrics
        psnr = 20*np.log10(1.0 / np.sqrt(np.mean(error**2)))

        # Histogram
        hist_orig, _ = np.histogram(img, bins=256)
        hist_quant, _ = np.histogram(img_quantized, bins=levels)

        return {
            'original': img,
            'quantized': img_quantized,
            'error': error,
            'banding_map': banding_map,
            'histogram': {'original': hist_orig, 'quantized': hist_quant},
            'psnr': psnr,
            'levels': levels
        }
```

### Extension Ideas
1. **Real Image Upload**: Allow user to upload photo, apply quantization, compare quality at different bit depths
2. **Perceptual Weighting**: Use contrast sensitivity function (CSF) to weight errors based on human vision
3. **Video Quantization**: Apply quantization to video sequence; show temporal flickering artifact
4. **Audio Quantization**: Play audio at different bit depths (8-bit, 16-bit, 24-bit) to demonstrate audio degradation
5. **Logarithmic Companding**: Compare uniform quantization to µ-law/A-law used in telephony

---

## Simulation: Discrete-Time Sampling Sequence Reconstructor

### Lecture Source: Lecture 22, Pages 8-11

### Visual Cues Observed
- Discrete-time sampling diagram: x[n] from wider-band continuous sequence with visible time gaps
- Progressive refinement images using DT sampling: capitol building shown at multiple resolution levels (original → downsampled → reconstructed)
- Multiple stages of downsampling shown with intermediate images progressively reducing resolution
- Frequency domain representation of DT signals showing spectral copies within [-π, π]

### Learning Objective
Visualize discrete-time sampling (downsampling and upsampling), understand aliasing in discrete sequences, and see practical application to image/video processing.

### Theoretical Foundation
DT sampling: y[n] = x[Mn] (keep every Mth sample) causes spectral copies to fold within [-π, π].
Reconstruction via upsampling and interpolation: insert zeros, then filter with interpolation kernel.
Aliasing in DT: if signal occupies bandwidth > π/M radians, downsampling by M causes aliasing.
Practical: images and video use DT downsampling for thumbnails/streaming.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Downsampling Factor M | 1-8 | Keep every Mth sample | Slider |
| Original Sampling Rate | Fixed | Reference (e.g., 1.0 normalized) | Display |
| Interpolation Method | Nearest, Linear, Cubic, Sinc | Reconstruction filter kernel | Select |
| Anti-Alias Before Down | true/false | Apply LPF before downsampling | Toggle |
| Upsampling Factor | 1-8 | Insert zeros and interpolate | Slider |
| Input Signal Type | Image, Synthetic Pattern, Real Video | Source data | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Original Signal | Full-res image or video frame | Input data |
| Downsampled Signal | M-fold reduced resolution | Shows aliasing if no anti-alias filter |
| Reconstructed Signal | Interpolated back to original size | Result after up-sampling and filtering |
| Frequency Response | DT spectrum [0, 2π] or [-π, π] | Show spectral replication in DT domain |
| Difference Image | Original - Reconstructed | Quantify reconstruction error |
| Blur Metrics | Frequency-domain sharpness measure | How much high-freq content lost |

### Visualization Strategy
- Three-panel layout (top row):
  - Original image (full resolution)
  - Downsampled by M (visible aliasing artifacts if no pre-filter)
  - Reconstructed by upsampling and interpolation
- Controls:
  - Slider for downsampling factor M (1-8); real-time update
  - Toggle anti-aliasing LPF on/off to compare aliasing vs. smooth downsampling
  - Select interpolation method to see quality differences (nearest → linear → cubic → sinc)
- Frequency domain subplot:
  - DT spectrum of downsampled signal showing folded copies if aliasing present
  - Highlight the effect of anti-aliasing filter
- Artifact indicators:
  - Checkerboard pattern shows aliasing texture when M too large without pre-filtering
  - Blur when sinc or cubic interpolation is used

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- Downsampling: y[n] = x[M*n] (simple indexing)
- Anti-aliasing: apply 1D LPF along rows/columns before downsampling
- Interpolation:
  - Nearest: x_interp[n] = x[floor(n/M)]
  - Linear: interpolate between adjacent samples
  - Cubic: use cubic spline basis functions
  - Sinc: convolve with sinc kernel (or use FFT-based perfect reconstruction)
- Metrics: compute 2D FFT, measure energy in high-frequency bands

**Code Outline:**
```python
class DTSamplingReconstructor(BaseSimulator):
    def _compute(self):
        # Load image
        img_orig = self._load_image(self.input_type)

        # Anti-alias filter if enabled
        if self.anti_alias:
            # Apply 2D Gaussian or sinc LPF
            cutoff_spatial = 1/self.M  # Normalized cutoff for DT
            img_filtered = self._apply_2d_lpf(img_orig, cutoff_spatial)
        else:
            img_filtered = img_orig

        # Downsample
        img_down = img_filtered[::self.M, ::self.M]

        # Upsample and interpolate
        h, w = img_orig.shape[:2]
        img_up = np.zeros((h, w))
        for i in range(0, h, self.M):
            for j in range(0, w, self.M):
                img_up[i, j] = img_down[i//self.M, j//self.M]

        # Interpolate
        if self.interp_method == "Nearest":
            img_recon = self._nearest_interp_2d(img_up, self.M)
        elif self.interp_method == "Linear":
            img_recon = self._linear_interp_2d(img_up, self.M)
        elif self.interp_method == "Cubic":
            img_recon = self._cubic_interp_2d(img_up, self.M)
        elif self.interp_method == "Sinc":
            img_recon = self._sinc_interp_2d(img_up, self.M)

        # Error
        error = np.abs(img_orig - img_recon)

        # Frequency domain
        F_orig = np.fft.fft2(img_orig)
        F_down = np.fft.fft2(img_down)

        return {
            'original': img_orig,
            'downsampled': img_down,
            'reconstructed': img_recon,
            'error': error,
            'freq_orig': np.abs(F_orig),
            'freq_down': np.abs(F_down),
            'metrics': {'psnr': self._compute_psnr(img_orig, img_recon)}
        }
```

### Extension Ideas
1. **Multi-Level Pyramid**: Show Gaussian or Laplacian pyramid (repeated downsampling with blurring)
2. **Video Temporal Sampling**: Apply downsampling in time (every M frames) to show motion aliasing
3. **Sinc vs. Interpolation Comparison**: A/B view with detailed frequency response of each method
4. **Custom Anti-Alias Filter**: Let user design LPF (Butterworth, sinc window) before downsampling
5. **Streaming Simulator**: Progressively refine image by downloading lower-res version first, then higher-res overlays

---

## Simulation: Modulation Scheme Comparator (AM/FM/PM)

### Lecture Source: Lectures 23-24, Pages 1-6

### Visual Cues Observed
- Block diagrams showing AM modulation: message + carrier = amplitude-modulated output
- Time-domain waveforms: baseband message x(t), carrier cos(ω_c*t), and modulated y(t) = x(t)cos(ω_c*t)
- Frequency domain: message spectrum X(jω) and modulated spectrum Y(jω) centered at ±ω_c
- PM formula: y(t) = cos(ω_c*t + k*x(t)) — phase is modulated by message
- FM formula: y(t) = cos(ω_c*t + k∫x(τ)dτ) — frequency is modulated by message
- Synchronous demodulation block diagram for AM recovery

### Learning Objective
Compare three modulation schemes (AM, PM, FM) visually, understand bandwidth expansion, and see practical tradeoffs.

### Theoretical Foundation
**AM:** y(t) = [1 + m*x(t)]*cos(ω_c*t), where m is modulation index. Bandwidth = 2*B_x.
**PM:** y(t) = cos(ω_c*t + k*x(t)). Bandwidth depends on peak phase deviation.
**FM:** y(t) = cos(ω_c*t + k*∫x(t)dt). Bandwidth given by Carson's rule: B_FM ≈ 2(Δf + f_m) where Δf = k*max(x).

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Message Frequency | 100 Hz - 5 kHz | Baseband signal frequency | Slider |
| Message Type | Sinusoid, Chirp, Music, Speech | Test signal | Select |
| Carrier Frequency | 1-100 MHz (normalized) | RF center frequency | Slider |
| Modulation Type | AM, PM, FM | Scheme to use | Radio button |
| Modulation Index (AM) | 0-1 | m in [1 + m*x(t)]*cos(...) | Slider |
| Modulation Index (PM/FM) | 0-10 | k in phase/frequency modulation | Slider |
| Display Mode | Time, Frequency, Constellation, Waterfall | Output visualization | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Message Signal x(t) | Baseband waveform plot | Input to modulator |
| Carrier Signal | Cos(ω_c*t) plot (zoomed to show cycles) | RF reference |
| Modulated Signal y(t) | Modulated waveform (envelope visible for AM) | RF output |
| Time-Domain Envelope | Traced amplitude of modulated signal | For AM: should match message |
| Spectrum Y(jω) | Magnitude spectrum showing replicas at ±ω_c | Bandwidth usage |
| Instantaneous Frequency | f_i(t) = ω_i(t)/(2π) for PM/FM | Shows frequency variation |
| Phase Trajectory | Unwrapped phase φ(t) | Cumulative phase modulation |

### Visualization Strategy
- Multi-panel display:
  - Top: Message signal x(t) and carrier cos(ω_c*t) (time axis allows zooming)
  - Middle: Modulated signal y(t) with high time resolution (shows RF oscillations)
  - Bottom-left: Frequency spectrum |Y(jω)| showing bandwidth occupied
  - Bottom-middle: Time-varying phase φ(t) (for PM/FM)
  - Bottom-right: Instantaneous frequency f_i(t) (useful for FM)
- Toggle between modulation types to see side-by-side comparison
- Sliders:
  - Message frequency: watch spectrum shift left/right
  - Modulation index: increases bandwidth (FM wider than AM for same index)
  - Carrier frequency: shifts spectrum around
- Overlay: mark Carson's bandwidth, Nyquist frequency, channel bandwidth limits
- Animation: simulate demodulation process (multiply by carrier, low-pass filter)

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- AM: y(t) = (1 + m*x(t))*cos(ω_c*t)
- PM: y(t) = cos(ω_c*t + k*x(t))
- FM: y(t) = cos(ω_c*t + k*∫x(τ)dτ); use cumsum or ODE integration
- Instantaneous frequency: f_i(t) = ω_c/(2π) + (k/(2π))*x(t) [for FM]
- Bandwidth: compute FFT magnitude, find -3dB width
- Demodulation: multiply by cos(ω_c*t), low-pass filter result

**Code Outline:**
```python
class ModulationComparator(BaseSimulator):
    def _compute(self):
        # Generate message
        t = np.linspace(0, 1/self.f_msg, 5000)
        if self.msg_type == "Sinusoid":
            x = np.cos(2*np.pi*self.f_msg*t)
        elif self.msg_type == "Chirp":
            x = np.sin(2*np.pi*self.f_msg*t*(1 + t))
        # ...

        # Generate modulated signals
        if self.mod_type == "AM":
            y = (1 + self.m*x) * np.cos(2*np.pi*self.f_c*t)
        elif self.mod_type == "PM":
            y = np.cos(2*np.pi*self.f_c*t + self.k*x)
        elif self.mod_type == "FM":
            phase = 2*np.pi*self.f_c*t + self.k*np.cumsum(x)*(t[1]-t[0])
            y = np.cos(phase)

        # Compute spectrum
        Y_fft = np.fft.fft(y)
        freqs = np.fft.fftfreq(len(t), t[1]-t[0])

        # Instantaneous frequency for PM/FM
        if self.mod_type in ["PM", "FM"]:
            phase_unwrapped = np.unwrap(np.angle(np.exp(1j*self.k*np.cumsum(x))))
            f_inst = np.gradient(phase_unwrapped, t) / (2*np.pi) + self.f_c
        else:
            f_inst = None

        return {
            'time': t,
            'message': x,
            'modulated': y,
            'spectrum': {'freqs': freqs, 'mag': np.abs(Y_fft)},
            'instantaneous_frequency': f_inst
        }
```

### Extension Ideas
1. **Superheterodyne Receiver Simulator**: Build a receiver that mixes down to IF, filters, and demodulates
2. **Noise Robustness**: Add AWGN at adjustable SNR; show demodulation errors for each scheme
3. **Multi-Tone Modulation**: Modulate multiple message channels at different ω_c frequencies; show FDM
4. **Digital Modulation**: Extend to BPSK, QPSK, QAM (discrete constellation points)
5. **Real Audio AM/FM Radio**: Load actual speech/music, modulate, and play back through speaker

---

## Simulation: Sampling Rate Conversion Visualizer

### Lecture Source: Lecture 22, Pages 8-11

### Visual Cues Observed
- Images downsampled progressively (original Capitol → small thumbnails)
- Frequency domain showing aliasing copies in downsampled version
- Progressive refinement images showing improved reconstruction quality
- Upsampling with interpolation bringing image back to original size

### Learning Objective
Understand sampling rate conversion (upsampling/downsampling), anti-aliasing requirements, and interpolation quality trade-offs in practical signal processing.

### Theoretical Foundation
Downsampling by M: y[n] = x[M*n] causes aliasing if signal not bandlimited to π/M.
Upsampling by L: insert L-1 zeros between samples, then filter with cutoff at π/L.
Practical design: polyphase filters for efficient multi-rate processing.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Initial Sample Rate | 48, 96, 192 kHz | Starting DT domain | Select |
| Target Sample Rate | 8, 16, 44.1, 48, 96, 192 kHz | Desired output rate | Select |
| Conversion Ratio | Computed | L/M = target/initial | Display |
| Anti-Alias Before Down | true/false | Prevent aliasing | Toggle |
| Interpolation Quality | Low, Medium, High | Kernel resolution | Select |
| Input Signal | Audio clip, Synthetic, Video frame | Source data | Select |
| Display Mode | Waveform, Spectrum, Image | What to show | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Input Signal | Original waveform or image | Baseline |
| Downsampled (Pre-Filter) | Signal at reduced rate with pre-filtering | Shows anti-aliasing effectiveness |
| Downsampled (No Pre-Filter) | Signal at reduced rate without filter | Shows aliasing artifacts |
| Upsampled/Interpolated | Reconstructed to target rate | Final output quality |
| Spectrum Comparison | Input, downsampled, reconstructed | Frequency domain view of artifacts |
| Error Signal | Difference between input and output | Quantify reconstruction error |
| Quality Metrics | SNR, THD, frequency response | Objective measures |

### Visualization Strategy
- Four-panel signal chain view:
  - Original signal/image
  - Anti-aliased version (if enabled)
  - Downsampled version
  - Reconstructed (upsampled + interpolated)
- Frequency domain subplot showing spectral evolution
- Toggle anti-aliasing on/off to show aliasing artifacts appear/disappear
- Slider to adjust interpolation quality
- Metrics box: displays SNR, alias tone frequency (if present), and quality rating

### Implementation Notes
**Complexity:** Medium

**Key Algorithms:**
- Downsampling: simple indexing y[n] = x[M*n]
- Anti-aliasing: design LPF with cutoff at π/M, apply before downsampling
- Upsampling: insert zeros, then convolve with interpolation filter
- Polyphase: pre-compute separate filters for each fractional delay
- Metrics: compute spectral distortion, THD from aliased frequencies

---

## Simulation: AM Radio Receiver Block Diagram (with Demodulation)

### Lecture Source: Lecture 23, Pages 5-6; Lecture 24, Pages 1

### Visual Cues Observed
- AM Communication System block diagram: message signal → [modulator] → transmitted AM signal
- Receiver block diagram: antenna → [RF amplifier] → [mixer with local oscillator] → [IF filter] → [AM demodulator] → [LPF] → output
- Synchronous demodulation: multiply by cos(ω_c*t), filter out double-frequency term
- Superheterodyne receiver: use intermediate frequency (IF) for better filtering and selectivity

### Learning Objective
Build an interactive AM radio receiver, understand the role of each stage (RF amp, mixer, IF filter, demodulator), and see impact of component choices on quality.

### Theoretical Foundation
AM transmission: y(t) = [A + m*x(t)]*cos(ω_c*t)
Receiver tasks: tune to carrier freq, amplify, filter out adjacent channels (IF bandpass), demodulate, recover baseband.
Synchronous demodulation: multiply received signal by cos(ω_c*t), LPF to recover m*x(t) + DC.
Local oscillator: must be phase-locked to carrier frequency for proper demodulation.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Tuning Frequency | 530-1710 kHz (AM band) | Receiver center frequency (sets LO) | Slider (large) |
| RF Gain | 0-30 dB | Input amplifier gain | Slider |
| IF Bandwidth | 5-15 kHz | Selectivity of channel filter | Slider |
| Demodulator Type | Synchronous, Envelope | Recovery method | Radio button |
| LO Phase Offset | -π to π | Demod carrier phase error | Slider |
| Channel Interference | None, Adjacent, Strong | Simulated other stations | Select |
| Input Source | Single Station, Multi-station Mix | Received signal | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Received RF Signal | Time-domain waveform (sparse plot) | What antenna sees |
| After RF Amp | Magnified RF signal | Shows gain effect |
| IF Signal | Baseband-like signal after mixer | Filtered around fIF |
| Demodulated Output | Recovered baseband | Should match original message |
| Spectrum RF | Frequency domain of received signal | Shows all stations in band |
| Spectrum IF | Narrowband filter output | Channel selection |
| Spectrum Baseband | Final recovered message spectrum | Audio band (100 Hz - 5 kHz) |
| Constellation Diagram | In-phase vs Quadrature (for sync demod) | Phase synchronization quality |

### Visualization Strategy
- Block diagram with interactive elements:
  - Antenna input → RF amp stage with gain slider
  - Mixer with local oscillator frequency slider (tuning dial)
  - IF bandpass filter with adjustable BW
  - AM demodulator (sync or envelope)
  - Audio LPF and output
- Three spectral views stacked vertically:
  - RF spectrum (full AM band, 530-1710 kHz) with tuning marker
  - IF spectrum (zoomed to ±BW/2 around fIF)
  - Baseband spectrum (DC to audio BW)
- Time-domain waveforms at RF, IF, and baseband
- Waterfall plot of frequency content as user tunes dial
- Audio playback: actual speaker output of demodulated message

### Implementation Notes
**Complexity:** Medium to High

**Key Algorithms:**
- Heterodyne mixing: multiply by cos(2π*f_LO*t) to shift spectrum down
- IF filtering: bandpass filter centered at standard IF frequency (455 kHz or 10.7 MHz)
- AM demodulation options:
  - Synchronous: multiply by cos(2π*f_c*t), low-pass filter (requires carrier recovery)
  - Envelope: rectify and low-pass filter (simpler, used in old radios)
- Phase error effect: LO phase offset ε reduces demod output amplitude by cos(ε)
- Adjacent channel rejection: IF filter BW controls attenuation of nearby stations

**Code Outline:**
```python
class AMRadioReceiver(BaseSimulator):
    def _compute(self):
        # Generate multi-station received RF signal (at antenna)
        t = np.linspace(0, 0.01, 50000)

        # Multiple AM-modulated signals at different frequencies
        stations = []
        for fc, message_text in [
            (600e3, "Station 1"),
            (750e3, "Station 2"),
            (900e3, self.tuned_message)
        ]:
            msg = self._generate_audio_from_text(message_text)
            am_signal = (1 + 0.5*msg) * np.cos(2*np.pi*fc*t)
            stations.append(am_signal)

        y_rf = np.sum(stations, axis=0) + 0.01*np.random.randn(len(t))  # Add noise

        # RF amplification
        y_rf_amp = self.rf_gain * y_rf

        # Mixer: multiply by LO at tuned frequency
        f_lo = self.tuned_freq
        y_mixed = y_rf_amp * np.cos(2*np.pi*f_lo*t + self.lo_phase_error)

        # IF filtering (bandpass around IF = |f_lo - f_sig|)
        f_if = 455e3  # Standard IF
        y_if = self._apply_if_filter(y_mixed, f_if, self.if_bandwidth)

        # AM demodulation
        if self.demod_type == "Synchronous":
            # Multiply by recovered carrier (assumes PLL locks)
            y_demod = 2*y_if * np.cos(2*np.pi*f_if*t)
        else:  # Envelope detection
            y_demod = np.abs(signal.hilbert(y_if))

        # Audio LPF
        y_audio = self._apply_audio_lpf(y_demod, 5000)

        # Compute spectra
        Y_rf = np.fft.fft(y_rf)
        Y_if = np.fft.fft(y_if)
        Y_audio = np.fft.fft(y_audio)

        return {
            'rf_signal': {'t': t, 'y': y_rf},
            'if_signal': {'t': t, 'y': y_if},
            'audio_signal': {'t': t, 'y': y_audio},
            'spectra': {
                'rf': {'freqs': freqs, 'mag': np.abs(Y_rf)},
                'if': {'freqs': freqs - f_if, 'mag': np.abs(Y_if)},
                'audio': {'freqs': freqs, 'mag': np.abs(Y_audio)}
            }
        }
```

### Extension Ideas
1. **Automatic Gain Control (AGC)**: Show how RF gain is automatically adjusted to maintain constant IF output level
2. **Phase-Locked Loop (PLL)**: Visualize carrier frequency recovery loop to lock onto weak signals
3. **Multi-Station Tuning**: Graphical "radio dial" showing all stations in AM band; click to tune
4. **Interference Mitigation**: Add notch filter to remove strong adjacent-channel or in-band interferer
5. **Digital vs. Analog Demod**: Compare analog envelope detector with digital synchronous demodulation quality

---

## Simulation: Phase-Locked Loop Frequency Tracker

### Lecture Source: Lecture 24, Pages 7-11

### Visual Cues Observed
- Phase/Frequency Modulation waveforms showing instantaneous phase φ(t) and instantaneous frequency ω_i(t)
- Frequency deviation: Δω = k*x(t) where x(t) is the message
- PLL block diagram: phase detector → loop filter → VCO
- Focusing with feedback control diagram showing tracking behavior

### Learning Objective
Understand phase-locked loops (PLLs) for frequency tracking, and see how feedback maintains lock on a time-varying frequency target.

### Theoretical Foundation
PLL: phase detector compares input phase to VCO output, error drives loop filter, which adjusts VCO frequency.
Lock condition: when VCO frequency matches input frequency, phase error is zero.
Loop dynamics: natural frequency ω_n and damping ratio ζ control settling time and overshoot.
FM demodulation: PLL output controls VCO frequency, recovering the frequency modulation information.

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Signal Frequency | 100 Hz - 10 kHz | Input signal or modulation | Slider |
| Frequency Deviation | 0-5 kHz | Δf = frequency swing (FM) | Slider |
| Loop Natural Freq ω_n | 10-1000 rad/s | PLL bandwidth | Slider |
| Damping Ratio ζ | 0.1-2.0 | Determines overshoot | Slider |
| Loop Filter Type | PI, Lead-Lag, Other | Loop dynamics | Select |
| Phase Error Injection | 0-π | Initial phase offset | Slider |
| Input Type | Sinusoid, Chirp, FM Modulated | Test signal | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Input Frequency | f_in(t) = ω_in(t)/(2π) | Target frequency (may be time-varying) |
| VCO Output Frequency | f_vco(t) | Feedback frequency from PLL |
| Phase Error | φ_error(t) = φ_in - φ_vco | Difference signal driving loop |
| Loop Filter Output | Control voltage to VCO | Shows corrective action |
| Phase Trajectories | φ_in(t) and φ_vco(t) on circle | 2D phase space |
| Lock Status | Boolean or metric | Whether PLL is locked |
| Step Response | Settling to frequency step | Shows overshoot, settling time |
| Frequency Sweep | Locus on phase plane as freq changes | Shows lock range and tracking |

### Visualization Strategy
- Multi-panel interactive display:
  - Top: Input and VCO frequency time-domain plot with overlay
  - Middle-left: Phase error φ_error(t) showing convergence to zero
  - Middle-right: Loop filter output (control voltage)
  - Bottom: 2D phase diagram (φ_in vs φ_vco) with trajectory
- Controls:
  - Slider for ω_n: see faster settling (higher BW) vs. oscillation (underdamped)
  - Slider for ζ: adjust damping from underdamped (overshoot) to overdamped
  - Frequency step or chirp to observe transient response
- Metrics:
  - Lock time: how long to acquire phase/frequency lock
  - Lock range: max frequency deviation PLL can track
  - Phase error steady-state: residual error at constant frequency

### Implementation Notes
**Complexity:** High

**Key Algorithms:**
- Phase detector: tan^{-1}(sin(φ_error)) or simple sin(φ_error) approximation
- Loop filter (PI): u(t) = K_p*φ_e + K_i*∫φ_e dt
- VCO: ω_vco = ω_0 + K_vco*u(t)
- Numerical integration: use ODE solver (RK4) to simulate dynamics
- Lock detection: monitor |φ_error| < threshold over time window

**Code Outline:**
```python
class PhaseLlockedLoopTracker(BaseSimulator):
    def _compute(self):
        # Input signal with time-varying frequency
        t = np.linspace(0, 1, 5000)

        if self.input_type == "Sinusoid":
            phi_in = 2*np.pi*self.f_signal*t
        elif self.input_type == "FM Modulated":
            # Frequency modulation: f(t) = f_c + Δf*cos(ω_m*t)
            f_inst = self.f_signal + self.f_dev*np.cos(2*np.pi*self.f_mod*t)
            phi_in = np.cumsum(f_inst)*(t[1]-t[0])*2*np.pi

        y_in = np.cos(phi_in + self.phase_offset)

        # PLL simulation using ODE
        def pll_dynamics(state, t_val, y_in_interp):
            phi_vco, omega_vco = state

            # Phase error
            y_vco = np.cos(phi_vco)
            phase_error = np.arctan2(y_in_interp(t_val), y_vco)  # Phase detector

            # Loop filter (PI)
            self.integral_error += phase_error*(t[1]-t[0])
            u = self.K_p*phase_error + self.K_i*self.integral_error

            # VCO
            omega_new = self.omega_0 + self.K_vco*u

            return [omega_new, 0]  # dphi/dt = omega, domega/dt = 0

        # Solve ODE
        y_in_interp = interp1d(t, y_in)
        phi_vco_list, omega_vco_list = [], []
        state = [self.phase_offset, self.omega_0]

        for t_val in t:
            dstate = pll_dynamics(state, t_val, y_in_interp)
            state[0] += dstate[0]*(t[1]-t[0])  # Euler step
            state[1] = self.omega_0 + self.K_vco*error  # Update omega
            phi_vco_list.append(state[0])
            omega_vco_list.append(state[1])

        phi_vco = np.array(phi_vco_list)
        omega_vco = np.array(omega_vco_list)
        y_vco = np.cos(phi_vco)

        # Phase error
        phi_error = phi_in - phi_vco

        # Frequency from phase derivative
        f_in = np.gradient(phi_in, t)/(2*np.pi)
        f_vco = np.gradient(phi_vco, t)/(2*np.pi)

        return {
            'time': t,
            'input_phase': phi_in,
            'vco_phase': phi_vco,
            'phase_error': phi_error,
            'input_freq': f_in,
            'vco_freq': f_vco,
            'vco_output': y_vco
        }
```

### Extension Ideas
1. **PLL Design Tool**: Let user adjust ω_n and ζ, see Bode plots and step response of closed loop
2. **FM Demodulator**: Use PLL output to decode frequency-modulated signal, recover original message
3. **Frequency Locked Loop (FLL)**: Simpler than PLL, uses frequency error instead of phase error
4. **Acquisition vs. Tracking**: Show pull-in range and hold-in range behavior
5. **Jitter Analysis**: Add phase noise to input; measure output jitter vs. loop BW

---

## Simulation: CD Audio Pipeline (Sampling + Quantization + Reconstruction)

### Lecture Source: Lecture 25, Pages 1-13

### Visual Cues Observed
- CD structure diagram: 1.8 µm tracks, 0.83-3.56 µm pits and lands, reflective layer, protective layer
- Audio pipeline: Continuous audio → Anti-aliasing filter → Sample and hold → ADC (quantization) → DT signal
- Sampling rate diagram: f_s = 44.1 kHz for CD audio
- Anti-aliasing filter cutoff shown at ~20 kHz (Nyquist frequency for CD)
- Quantization: 16-bit → 2^16 = 65,536 levels for amplitude resolution
- Reconstruction: DT → interpolation → reconstruction filter → analog audio
- Focus: Interharmonic testing with pits translating to 1 and 0 bits

### Learning Objective
Demonstrate the complete CD audio pipeline, integrating sampling, anti-aliasing, quantization, and reconstruction to show how analog audio is stored digitally and recovered.

### Theoretical Foundation
CD audio standard: 44.1 kHz sampling (Nyquist criterion: 44.1/2 = 22.05 kHz covers 20 Hz - 20 kHz human hearing)
Anti-aliasing: steep LPF removes >22 kHz content before sampling
Quantization: 16-bit linear PCM, approximately 96 dB dynamic range
Reconstruction: D/A converter (often with upsampling/interpolation filters internally)
Pit encoding: pits and lands are read as 1 and 0 bits; CIRC error correction codes added

### System Architecture

**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|-----------|
| Input Audio | Music Clip, Chirp, Synthetic, Microphone | Source signal | Select |
| Sampling Rate | 44.1, 48, 96, 192 kHz | Samples per second | Select |
| Bit Depth | 8, 16, 24, 32 bit | Quantization resolution | Select |
| Anti-Alias Cutoff | 0.4-0.95*(f_s/2) | LPF stopband edge | Slider |
| Anti-Alias Type | Ideal, Butterworth, Elliptic | Filter family | Select |
| Quantization Type | Uniform, Dithered | Amplitude rounding method | Select |
| Dither Strength | 0-1 LSB | Dither noise amplitude | Slider |
| Reconstruction Type | Zero-hold, Linear, Sinc, Cubic | Interpolation method | Select |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Original Audio | Time-domain waveform | Analog input |
| Anti-Aliased Audio | Filtered waveform | Pre-sampling signal |
| Sampled Signal | Discrete points x[n] | DT representation |
| Quantized Signal | Rounded to grid | 16-bit (or chosen) levels |
| Quantization Error | x[n] - x_q[n] | Error magnitude and spectrum |
| Reconstructed Audio | Interpolated signal | D/A output |
| Reconstruction Error | Original - reconstructed | Fidelity loss |
| Frequency Responses | Anti-alias filter, reconstruction filter | Magnitude and phase |
| SNR Metric | dB | Signal-to-quantization-noise ratio |
| Spectrogram | Time-frequency plot of audio | Shows spectral content evolution |

### Visualization Strategy
- Signal chain view (vertical stacking):
  1. Input analog audio with frequency response
  2. After anti-aliasing filter (shows attenuation above 22 kHz)
  3. Sampled signal (dots at f_s = 44.1 kHz spacing)
  4. Quantized signal (rounded to 16-bit levels; show quantization error)
  5. Reconstructed audio after D/A and reconstruction filter
  6. Final output (should closely match input, with some quantization noise)
- Frequency domain tabs:
  - Input spectrum (0-96 kHz)
  - After anti-aliasing (attenuated above 22 kHz)
  - Sampled spectrum (replicas visible)
  - Quantized spectrum (noise floor raised slightly)
  - Reconstructed spectrum (cleanup by reconstruction filter)
- Metrics display:
  - THD (total harmonic distortion)
  - SINAD (signal-to-noise and distortion ratio)
  - SNR (signal-to-noise ratio)
  - Dynamic range (dB)
- Play buttons: play original audio and reconstructed audio for subjective listening comparison

### Implementation Notes
**Complexity:** High

**Key Algorithms:**
- Anti-aliasing: design LPF with cutoff at 0.9*f_s/2 (leave margin)
- Sampling: x[n] = x(n/f_s) at exact sample times
- Quantization: x_q = round(x*2^{b-1})/2^{b-1} for b-bit uniform
- Dithering: add triangular dither noise before quantization
- Reconstruction: upsample (insert zeros), apply reconstruction LPF (often 4x oversampling internally in CD players)
- Error metrics: compute SNR = 10*log10(P_signal / P_noise)

**Code Outline:**
```python
class CDaudioPipeline(BaseSimulator):
    def _compute(self):
        # Load or generate audio
        audio = self._load_audio(self.input_audio)
        t = np.linspace(0, len(audio)/self.f_s_orig, len(audio))

        # Resample if needed to target f_s
        if self.f_s != self.f_s_orig:
            audio = resample(audio, int(len(audio)*self.f_s/self.f_s_orig))
            t = np.linspace(0, len(audio)/self.f_s, len(audio))

        # Anti-aliasing filter
        nyquist = self.f_s/2
        audio_filtered = self._apply_lpf(audio, self.aa_cutoff, self.aa_type, self.aa_order)

        # Sampling (already discrete at this point, but show the concept)
        # Sample at t[n] = n/f_s
        audio_sampled = audio_filtered  # Already sampled

        # Quantization
        levels = 2**self.bit_depth
        if self.quantize_type == "Dithered":
            dither = np.random.triangular(-self.dither_strength/(2*levels),
                                          0,
                                          self.dither_strength/(2*levels),
                                          len(audio_sampled))
            audio_dithered = audio_sampled + dither
        else:
            audio_dithered = audio_sampled

        # Quantize
        audio_q = np.round(audio_dithered*levels/2)/(levels/2)
        audio_q = np.clip(audio_q, -1, 1)

        # Compute error
        q_error = audio_filtered - audio_q

        # Reconstruction (interpolation + filter)
        audio_recon = self._apply_reconstruction_filter(audio_q, self.recon_type,
                                                        self.f_s, oversampling=4)

        # Compute metrics
        P_signal = np.mean(audio_filtered**2)
        P_noise = np.mean(q_error**2)
        snr_db = 10*np.log10(P_signal / (P_noise + 1e-10))

        # Spectra
        F_orig = np.fft.fft(audio_filtered)
        F_q = np.fft.fft(audio_q)
        F_recon = np.fft.fft(audio_recon)

        return {
            'original': {'t': t, 'audio': audio_filtered},
            'sampled': {'t': t, 'audio': audio_sampled},
            'quantized': {'t': t, 'audio': audio_q, 'error': q_error},
            'reconstructed': {'t': t, 'audio': audio_recon},
            'spectra': {
                'original': F_orig,
                'quantized': F_q,
                'reconstructed': F_recon
            },
            'metrics': {'snr_db': snr_db, 'thd': self._compute_thd(audio_q, audio_filtered)}
        }
```

### Extension Ideas
1. **Bitrate vs Quality Trade-off**: Show MP3/AAC compression on top of CD pipeline; compare file sizes
2. **Error Correction**: Demonstrate CIRC codes protecting against scratches (simulate bit flips)
3. **Pit Encoding**: Show how audio samples are encoded as pit patterns on CD surface
4. **Oversampling D/A**: Use 4x or 8x oversampling internally in reconstruction; show noise shaping benefit
5. **Real Album Mastering**: Load actual CD-quality audio file, show waveform, SNR, and THD characteristics

---

## Summary Table of Simulation Ideas

| ID | Simulation | Lecture(s) | Complexity | Key Visual Elements |
|----|-----------|-----------|-----------|-------------------|
| 1 | Spectral Replication Visualizer | 21 | Medium | Frequency domain replicas, Nyquist band highlighting |
| 2 | Anti-Aliasing Filter Designer | 21-22 | Medium-High | Bode plots, passband/stopband, phase response, group delay |
| 3 | Quantization Artifact Explorer | 22 | Medium | Image quantization levels, banding maps, dithering effect |
| 4 | DT Sampling Sequence Reconstructor | 22 | Medium | Multi-resolution images, upsampling/downsampling, interpolation kernels |
| 5 | Modulation Scheme Comparator (AM/FM/PM) | 23-24 | Medium | Time & frequency domain, instantaneous frequency, bandwidth comparison |
| 6 | Sampling Rate Conversion Visualizer | 22 | Medium | Polyphase filters, multi-rate signal processing, quality metrics |
| 7 | AM Radio Receiver Block Diagram | 23-24 | Medium-High | Heterodyne receiver, IF filtering, demodulation, constellation |
| 8 | Phase-Locked Loop Frequency Tracker | 24 | High | Phase plane, loop dynamics, transient response, lock range |
| 9 | CD Audio Pipeline (Complete) | 25 | High | Sampling → quantization → reconstruction chain, audio quality metrics |

---

## Implementation Roadmap

**Phase 1 (Foundation - Lectures 21-22):**
- Spectral Replication Visualizer
- Anti-Aliasing Filter Designer
- Quantization Artifact Explorer

**Phase 2 (Practical - Lectures 22-23):**
- DT Sampling Sequence Reconstructor
- Sampling Rate Conversion Visualizer

**Phase 3 (Communication - Lectures 23-24):**
- Modulation Scheme Comparator
- AM Radio Receiver Block Diagram

**Phase 4 (Advanced Control - Lecture 24):**
- Phase-Locked Loop Frequency Tracker

**Phase 5 (Integration - Lecture 25):**
- CD Audio Pipeline (Complete)
