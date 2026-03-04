# Novel Simulation Ideas from Lectures 21-25
## MIT 6.003 Signals and Systems

---

## Simulation: Nyquist Paradox Explorer
### Lecture Source: Lecture 21, Pages 12-19
### Learning Objective
Intuitively understand why different continuous-time signals can produce identical samples, and visualize the critical boundary where sampling information loss occurs. Students should grasp that the Nyquist rate isn't arbitrary but represents a fundamental frequency aliasing boundary.

### Theoretical Foundation
The Nyquist sampling theorem states: A bandlimited signal $x(t)$ with $X(j\omega) = 0$ for $|\omega| > \omega_m$ can be perfectly reconstructed from samples $x[n] = x(nT)$ if the sampling frequency $\omega_s = 2\pi/T > 2\omega_m$.

Key equations:
- Sampling frequency: $\omega_s = 2\pi/T$
- Nyquist frequency: $\omega_N = \omega_s/2 = \pi/T$
- Aliasing formula: $\omega_{alias} = |\omega_{in}| \pmod{\omega_s}$ (reflected into $[-\omega_s/2, \omega_s/2]$)
- Reconstruction condition: $\omega_{in} \leq \omega_N$ for perfect recovery

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Signal Frequency | 0.5 - 8 kHz | Frequency of primary sinusoid | Slider with linked marker |
| Sampling Rate | 1 - 16 kHz | fs; must exceed 2 × signal frequency for Nyquist | Slider with Nyquist line overlay |
| Number of Periods | 2 - 10 | Time window showing oscillations | Slider |
| Phase | 0 - 2π | Initial phase of signal | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Continuous Signal | Blue curve spanning full time axis | Show underlying true signal |
| Discrete Samples | Orange dots at sampling instants | Visualize point samples |
| Aliased Signal | Red dashed curve through samples | Reconstructed signal if aliasing occurs |
| Frequency Domain | Subplot showing original spectrum & sampled copies | Reveal aliasing in frequency domain |
| Alias Warning Indicator | Color badge (green safe/red danger) | Immediate feedback on Nyquist violation |

### Visualization Strategy
**Interactive Flow:**
1. Display continuous input signal with overlay of sample points
2. Allow user to adjust signal frequency freely
3. When $f_{signal} < f_s / 2$, show green "Safe - No Aliasing" badge and reconstruction matches original
4. When $f_{signal} > f_s / 2$, show red "Aliasing!" badge and display the aliased frequency (e.g., "Input 6 kHz → Aliases to 2 kHz")
5. Frequency domain subplot shows how each frequency copy appears at $\pm n f_s$ intervals
6. **"Aha moment":** User drags sampling rate slider down, watches as same samples could represent completely different signals near the Nyquist boundary

**Visual Cues:**
- Show the "Nyquist critical frequency" as a vertical green reference line in frequency domain
- When user reduces sampling rate below 2×signal frequency, samples suddenly ambiguous; animate the alternative aliased signal faintly
- Link time and frequency domains: hovering over a sample point highlights its harmonic contribution

### Implementation Notes
**Complexity:** Medium
**Key Algorithms:**
- FFT-based spectrum computation (scipy.fft)
- Aliasing detection: compare input frequency mod (fs/2) against fs/2
- Bandlimited reconstruction using sinc interpolation (for reference comparison)
- Real-time signal evaluation: $x[n] = A\sin(2\pi f_n T + \phi)$

**Dependencies:** NumPy, SciPy (FFT), Plotly for dual time/frequency plots

### Extension Ideas
**Beginner:** Add preset signals (cosine, square wave) and show how square wave high-frequency harmonics cause aliasing in lower bins
**Advanced:** Implement anti-aliasing filter slider; show how Butterworth LPF attenuates high frequencies before aliasing occurs
**Real-world:** Load a user's audio file, downsample it to various rates, play back samples to hear aliasing artifacts

---

## Simulation: Quantization & Perceptual Quality
### Lecture Source: Lecture 22-2, Pages 8-30
### Learning Objective
Understand how amplitude quantization (discrete levels) introduces error, why bit depth affects quality in non-linear ways, and how dithering + perceptual masking improve perceived quality without more bits. Students should develop intuition for the human ear's sensitivity to different artifacts.

### Theoretical Foundation
Quantization maps continuous amplitude to discrete levels. For $b$ bits, uniform quantization divides range $[-1, 1]$ into $2^b$ steps of size $\Delta = 2/2^b$.

Key relationships:
- Quantization error: $|e[n]| \leq \Delta/2$ (half-step)
- Signal-to-Noise Ratio: $SNR \approx 6.02b + 1.76$ dB (for full-scale sine)
- Dithering formula: $y[n] = Q(x[n] + d[n]) - d[n]$ where $d[n] \in [-\Delta/2, \Delta/2]$ is random dither
- Roberts' dithering: applies same dither before & after quantization to reduce noise shaping artifacts

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Bit Depth | 1-16 bits | Quantization resolution | Slider with audio preview |
| Dithering Mode | None / Random / Roberts | Noise addition strategy | Radio buttons |
| Signal Complexity | Sine / Speech / Music | Test signal (pre-loaded) | Dropdown selector |
| Audio Playback | Play/Stop | Real-time audio feedback | Button control |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Original Signal | Blue curve | Baseline analog signal |
| Quantized Signal | Stepped staircase overlay | Shows discrete levels |
| Error Signal | Green difference plot | Quantization error magnitude |
| Spectrogram | 2D frequency-time heatmap | Show noise shaping; reveal where error sits spectrally |
| Quality Metrics | SNR (dB), SINAD, Noise Floor | Quantitative assessment |

### Visualization Strategy
**Key Insight Sequence:**
1. **Setup:** Start with 16-bit, no dithering. Signal looks smooth.
2. **Degradation:** User reduces to 4 bits. Staircase effect visible, steps crude but perceptually tolerable for many signals.
3. **Artifact Zoom:** Show 8-bit image quantization side-by-side (banding effect in gradients) to build intuition across domains.
4. **Dithering Magic:** Switch on dithering at 4 bits. Visually appears more noise, BUT spectrogram shows noise spread uniformly across frequencies (better than banding). Audio sounds less "synthetic."
5. **Roberts Twist:** Toggle Roberts' dithering. Noise floor drops further; signal-dependent noise patterns minimize.

**Interactive Comparisons:**
- A/B playback toggle: compare 4-bit no dither vs. 4-bit with dither (reveals dithering value in hearing loss reduction)
- Zoom into waveform to see quantization levels directly
- Frequency zoom tools to inspect noise shape at different frequencies

### Implementation Notes
**Complexity:** Medium-High
**Key Algorithms:**
- Uniform quantizer: $y = \Delta \cdot \text{round}(x / \Delta)$
- Dither generation: `numpy.random.uniform(-Δ/2, Δ/2, len(x))`
- Spectrogram: `scipy.signal.spectrogram()` with window overlap
- Audio synthesis: scipy WAV generation for preview playback
- Error calculation: `quantization_error = original - quantized`

**Dependencies:** NumPy, SciPy (signal processing), Plotly, librosa (for music feature analysis)

### Extension Ideas
**Beginner:** Compare uniform vs. non-uniform (mu-law/A-law) quantization used in telephony
**Advanced:** Implement JPEG-style perceptual quantization (quantization matrix varies by frequency/DCT coefficient); show how human ear sensitivity to low frequencies justifies coarser high-frequency quantization
**Real-world:** Quantize speech at 8-bit (telephone quality), compare to 16-bit CD quality; explore trade-offs between storage size and perceived fidelity

---

## Simulation: Aliasing Frequency Mapper
### Lecture Source: Lecture 21, Pages 31-40
### Learning Objective
Develop intuitive mastery of the aliasing wrapping mechanism. Given an input frequency and sampling rate, students should predict the output alias frequency and understand aliasing as a "modular arithmetic" problem on the frequency axis.

### Theoretical Foundation
When sampling at rate $f_s$, input frequency $f_{in}$ aliases to:
$$f_{alias} = \begin{cases}
f_{in} & \text{if } 0 \leq f_{in} < f_s/2 \\
f_s - f_{in} & \text{if } f_s/2 < f_{in} < f_s \\
f_{in} - 2f_s & \text{if } f_s < f_{in} < 3f_s/2 \\
\vdots
\end{cases}$$

Intuition: frequency "folds" at multiples of $f_s/2$. A frequency above Nyquist reflects back down.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Input Frequency | 0 - 100 kHz | Unknown source frequency | Text input or slider |
| Sampling Rate | 1 - 50 kHz | Nyquist boundary at fs/2 | Text input or slider |
| Number of Replicas | 1 - 5 | How many spectral copies to show | Slider |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Frequency Axis Diagram | Linear axis 0 to fs with marked regions | Show Nyquist zone boundaries |
| Input Frequency Marker | Large dot at fin on extended axis | Identify input position |
| Nyquist Zones | Colored bands (-fs/2 to fs/2 = Zone 1, fs/2 to 3fs/2 = Zone 2, etc.) | Highlight folding regions |
| Aliased Frequency Marker | Highlighted dot in Zone 1 | Show where input maps after aliasing |
| Animated Path | Arrow tracing folding path | Visualize how frequency wraps/reflects |
| Formula Display | Dynamic text showing calculation steps | Teach the aliasing formula |

### Visualization Strategy
**Interactive Learning Path:**
1. **Setup:** Display extended frequency axis 0 to 2fs with Nyquist boundaries marked as vertical dashed lines
2. **Place Input:** User enters or drags fin on the extended axis
3. **Automatic Folding Animation:** Animated sequence shows fin "bouncing" at Nyquist boundaries until it lands in [-fs/2, fs/2]
4. **Step-by-Step Equation:** Display algebraic steps: "fin = 30 kHz, fs = 22 kHz → 30 > 22/2? Yes → fold: fs - (fin - fs) = 22 - 8 = 14 kHz"
5. **Music Application:** Harmonic example (pitch aliasing) from Lecture 21: 10 kHz signal, third harmonic at 30 kHz, sample at 44 kHz → show 30 kHz aliases to 14 kHz, explaining why pitch changes
6. **Backward Problem:** Reverse mode: given output alias frequency and fs, find all possible input frequencies (there are infinite!)

**Visual Feedback:**
- Color-code zones: Zone 1 (green/safe), Zone 2 (yellow/wraps), Zone 3+ (red/high wrapping)
- Show small preview spectrum above axis: original impulse + aliased copy at calculated location
- List all harmonics of a periodic signal and their aliases in a table (from Lecture 21, pages 35-39)

### Implementation Notes
**Complexity:** Low-Medium
**Key Algorithms:**
- Aliasing fold function: recursive reflection at each Nyquist boundary
- Zone detection: `zone = floor(fin / (fs/2))`
- Alias calculation: Use modular arithmetic and reflection symmetry
- Animation: Plotly frame-by-frame trajectory of frequency marker

**Dependencies:** NumPy, Plotly (for interactive annotations and animations)

### Extension Ideas
**Beginner:** Build a "guess the alias" game: given fin and fs, predict output; check answer
**Advanced:** Extend to 2D spatial aliasing (images); show Moiré patterns in downsampled photographs when Nyquist violated
**Real-world:** CD player aliasing (music sampled at 44.1 kHz, out-of-band noise aliases back into audio band); design anti-aliasing filter to prevent it

---

## Simulation: FM Bandwidth Evolution
### Lecture Source: Lecture 24, Pages 99-43
### Learning Objective
Viscerally understand how frequency modulation index (m) controls bandwidth and sidebands. Students should see that narrowband FM (m << 1) has similar bandwidth to AM, but wideband FM (m >> 1) trades bandwidth for noise robustness. Carson's rule should emerge naturally from observation.

### Theoretical Foundation
Frequency modulation: $y(t) = \cos(\omega_c t + m \sin(\omega_m t))$ where $m = \Delta \omega / \omega_m$ is the modulation index.

Key insights:
- Narrowband FM (m << 1): $y(t) \approx \cos(\omega_c t) - m\sin(\omega_m t)\sin(\omega_c t)$ → BW ≈ 2ω_m (like AM)
- Wideband FM: Infinite sidebands at $\omega_c \pm k\omega_m$ with amplitudes given by Bessel functions $J_k(m)$
- Carson's bandwidth rule: $BW \approx 2(\Delta\omega + \omega_m) = 2\omega_m(m + 1)$
- Power concentration: Most power in sidebands where $|J_k(m)| > 0.01$, which depends on m

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Modulation Index (m) | 0.1 - 20 | Ratio of frequency deviation to message frequency | Slider with log scale |
| Message Frequency (fm) | 100 Hz - 10 kHz | Frequency of modulating signal | Slider |
| Carrier Frequency (fc) | 10 kHz - 100 kHz | Center frequency of FM signal | Slider |
| Modulation Regime | Narrowband / Wideband | Toggle to highlight region of interest | Radio button |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Time-Domain Waveform | Instantaneous frequency sweep visible in signal | Show frequency modulation effect |
| Frequency Spectrum | Bar chart at fc ± k·fm with heights = |Jk(m)| | Display sideband structure |
| Bessel Function Plot | J0(m), J1(m), J2(m), ... curves overlaid | Show why sideband amplitudes change with m |
| Instantaneous Frequency | Color-coded time plot showing ωi(t) = dφ/dt | Visualize actual frequency deviation |
| Carson Bandwidth Indicator | Shaded region on spectrum marking BW bounds | Reference for comparison |
| Occupied Bandwidth | Dynamic calculation as % of Carson's rule | Quantify spectral efficiency |

### Visualization Strategy
**Discovery Sequence:**
1. **Start Narrowband (m = 0.5):**
   - Spectrum shows carrier + two small sidebands (k=±1 significant, rest negligible)
   - Carson's rule: BW = 2×fm×(0.5+1) = 3fm, close to AM bandwidth
   - Time waveform looks like AM with modulated amplitude (actually phase, but hard to see)

2. **Increase m Slowly (m → 2):**
   - More sidebands (k=±2) appear with |J2(m)| rising
   - Spectrum spreads; bandwidth grows toward Carson's BW = 6fm
   - Waveform increasingly "crowded" with oscillations

3. **Jump to Wideband (m = 10):**
   - Spectrum explodes: dozens of sidebands visible, each separated by fm
   - Carson's rule: BW ≈ 22fm (>10× narrowband)
   - Instantaneous frequency animates with large swings (±10fm)

4. **Interactive Bessel Overlay:**
   - Superimpose Bessel function curves J0, J1, J2, etc.
   - User sees that sideband at fc+k·fm has amplitude |Jk(m)|
   - As m increases, power distributes to higher-order sidebands (wider spectrum)

5. **Noise Resilience Argument (Qualitative):**
   - Red highlight: region where |Jk(m)| > 0.01 (occupied bandwidth)
   - Note that wideband FM spreads signal over larger frequency region, making it less vulnerable to narrowband noise
   - Link to Lecture 24, Page 44 intuition

**Interactive Features:**
- Slider for m continuously updates spectrum and time-domain plots
- Hovering over sideband shows k value and |Jk(m)| amplitude
- Toggle: show/hide Bessel functions, Carson's bounds, Nyquist zone
- Play synthesized audio: hear pitch modulation at different m values

### Implementation Notes
**Complexity:** Medium-High
**Key Algorithms:**
- FM synthesis: `y = cos(wc*t + m*sin(wm*t))`
- Bessel function J_k(m): `scipy.special.jv(k, m)`
- Fourier transform for spectrum: FFT of sampled FM signal
- Instantaneous frequency: `fi(t) = wc + m*wm*cos(wm*t)` (derivative of phase)
- Carson's bandwidth: `BW = 2*(m*wm + wm)` (in rad/s) or `2*(m*fm + fm)` (in Hz)

**Dependencies:** NumPy, SciPy (special.jv for Bessel), Plotly, librosa for audio synthesis

### Extension Ideas
**Beginner:** Implement and compare narrowband FM demodulator (discriminator); show recovered message quality degrades as m increases toward wideband
**Advanced:** Compute and plot noise figure (SNR_out vs SNR_in) for varying m; demonstrate SNR improvement in wideband FM vs AM (threshold effect)
**Real-world:** Tune an FM radio receiver; visualize how crystal oscillator stability affects received spectrum (frequency offset); design feedback loop for frequency lock

---

## Simulation: Dithering Artifact Explorer
### Lecture Source: Lecture 22-2, Pages 23-45
### Learning Objective
Understand how dithering trades quantization error pattern (banding) for white noise, and how Roberts' dithering further optimizes this trade. Students should recognize that visual/auditory artifacts depend on *spectrum* of error, not just magnitude.

### Theoretical Foundation
Quantization without dither: error is signal-dependent, causing visible banding in smooth gradients or audio "stair-stepping."

With dither: $y[n] = Q(x[n] + d[n]) - d[n]$ where $d[n]$ is random noise $\sim \text{Uniform}(-\Delta/2, \Delta/2)$
- Error becomes white noise (uniformly distributed across frequencies)
- Listeners perceive "dither hum" instead of harshness; often preferred even if SNR measured lower
- Roberts' method: $y[n] = Q(x[n] + d[n]) - d[n]$ where same $d[n]$ subtracted; reduces noise power further

Roberts formula: Subtract the exact dither added before quantization, leaving only the quantization boundary randomization.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Bit Depth | 2-8 bits | Resolution (deliberately coarse to show artifacts) | Slider |
| Dithering Method | None / Random / Roberts / Triangular | Error spectral shaping strategy | Button group |
| Test Pattern | Gradient / Sine Sweep / Speech | Visual or auditory test signal | Dropdown |
| Zoom Level | 1× - 16× | Magnification to see quantization details | Slider or zoom tool |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Original Image/Signal | Smooth input (gradient or smooth waveform) | Baseline without artifacts |
| Quantized Output | Resulting image with visible banding/noise | Show artifact morphology |
| Error Spectrogram | 2D heatmap of error spectrum over time | Visualize error distribution (white vs. colored) |
| Comparison Views | 3-panel: No Dither / Dither / Roberts | Side-by-side quality assessment |
| Perceptual Quality Slider | Subjective rating (visual/audio quality) | Engage intuition, not just math |
| Error Statistics | RMS error, Error Peak, Noise Floor | Quantitative metrics |

### Visualization Strategy
**Dual-Domain (Visual & Auditory) Demonstration:**

**Visual Path (Image Quantization):**
1. Start with 8-bit smooth gradient (no visible banding)
2. Reduce to 4-bit: crude bands appear
3. **Without dither:** Clean banding stripes (visible artifact)
4. **With random dither:** Appears noisier but banding gone (Lecture 22-2, pages 24-25)
5. **Roberts method:** Noise reduced, banding still absent, sweet spot
6. **Zoom tool:** Let student magnify regions to see pixel-level structure and dither pattern

**Auditory Path (Audio Quantization):**
1. Play 16-bit baseline (reference quality)
2. Degrade to 4-bit no dither: "synthetic," "crunchy," harsh distortion
3. Same 4-bit + random dither: "grainy," but tonality preserved (less objectionable to ear)
4. Roberts: "cleanest" 4-bit version
5. A/B playback toggle to compare two methods

**Linked Interactivity:**
- Histogram of error values: flat (white) for dithered, peaked at quantization boundaries for no-dither
- Spectrogram: show how undithered error concentrates energy at signal harmonics; dithered error spreads uniformly

### Implementation Notes
**Complexity:** Medium
**Key Algorithms:**
- Quantization: `y = Delta * np.round(x / Delta)`
- Dither generation: `d = np.random.uniform(-Delta/2, Delta/2, len(x))`
- Roberts: `y = np.round((x + d) / Delta) * Delta - d`
- Spectrogram: `scipy.signal.spectrogram(error, nperseg=256)`
- Error analysis: histogram, FFT, RMS calculation

**Dependencies:** NumPy, SciPy, Plotly, librosa (for audio synthesis), PIL/OpenCV (for image rendering)

### Extension Ideas
**Beginner:** Implement Floyd-Steinberg error diffusion dithering (for images); show how spatial error distribution creates texture
**Advanced:** Design optimal dither (noise shaping) to minimize perceptual error; compute noise floor of dithered signal using advanced spectral estimation
**Real-world:** A/D converter design: specify dither requirement for audio interface to achieve target SNR with given bit depth; compare analog dither circuits vs. digital dither injection

---

## Simulation: CD Audio Pipeline
### Lecture Source: Lecture 25, Pages 136-31
### Learning Objective
Understand the complete signal processing chain from analog microphone to CD bitstream: anti-aliasing, sampling at 176.4 kHz, downsampling to 44.1 kHz, quantization to 16-bit, and the role of each stage in preserving audio quality. Students should grasp why CD specs (44.1 kHz, 16-bit, 2 channels) are optimal for human hearing.

### Theoretical Foundation
CD encoding pipeline:
1. **Anti-aliasing filter:** Attenuate frequencies above fs/2 = 22.05 kHz to prevent aliasing
2. **High-rate sampling:** Initially sample at 176.4 kHz (4× the CD rate of 44.1 kHz) for headroom
3. **Downsampling:** Decimate from 176.4 to 44.1 kHz using DT filter + downsampling factor of 4
4. **Quantization:** Map amplitude to 16-bit (65,536 levels) via uniform quantizer
5. **Encoding:** Format as stereo samples, add error correction, encode to CD pits

Human hearing: frequency range 20 Hz – 20 kHz (upper limit variable; typically ~16 kHz for aging). 44.1 kHz Nyquist = 22.05 kHz, safely above 20 kHz.

### System Architecture
**Input Parameters:**
| Parameter | Range | Physical Meaning | UI Control |
|-----------|-------|------------------|------------|
| Original Sample Rate | 44.1 / 96 / 176.4 / 192 kHz | Source quality (CD vs. hi-res) | Dropdown |
| Anti-Aliasing Cutoff | 18 - 22 kHz | Filter edge frequency | Slider |
| Intermediate Sample Rate | 44.1 - 176.4 kHz | Rate before downsampling | Slider (4× or 2× CD rate) |
| Quantization Bits | 16-24 bits | Resolution (CD = 16) | Slider |
| Test Signal | Sine @ 1 kHz / Music / Speech | Input audio | Dropdown + upload option |
| Animate Pipeline | On/Off | Step through each stage | Toggle |

**Output Observables:**
| Observable | Visualization | Purpose |
|------------|----------------|---------|
| Original Spectrum | Blue curve from 0 - 100 kHz | Show all frequency content |
| Anti-Aliased Spectrum | Green curve with roll-off above 22 kHz | Visualize filter effect |
| Sampled Spectrum (176.4 kHz) | Replicas at ±176.4 kHz intervals | Show sampling (4× CD rate) |
| Downsampled Spectrum | Replicas at ±44.1 kHz intervals | Show final CD spectrum |
| Quantized Waveform | Stepped samples in time domain | Visualize 16-bit quantization |
| Signal Quality Metrics | SNR, THD, Nyquist Margin | Quantitative assessment |
| CD Bitstream Visualization | Mock pit/land pattern (animation) | Show final encoded format |

### Visualization Strategy
**Story-Driven Learning:**

**Chapter 1: Why Anti-Aliasing?**
- Display original spectrum (e.g., music with high-frequency content above 20 kHz)
- Warn: "Sampling at 44.1 kHz will alias frequencies > 22.05 kHz down into audible range"
- Show rollback of energy above 22 kHz with adjustable filter
- Calculate "Nyquist Margin": margin between signal bandwidth and Nyquist cutoff

**Chapter 2: Oversampling for Headroom**
- Explain: "Why sample at 176.4 kHz if only 44.1 kHz needed?"
- Answer: Relaxes anti-aliasing filter specs; easier (less sharp) analog filter required; more headroom in downsampling chain
- Visualize filter transition region: steep (hard to build) at 44.1 kHz; gentler (practical) at 176.4 kHz

**Chapter 3: Downsampling (DT Processing)**
- Animate the downsampling process: remove 3 of every 4 samples, then filter to suppress aliased copies
- Show before/after spectrum: before downsampling, signal occupies ±88.2 kHz; after, confined to ±22.05 kHz
- Highlight that downsampling is the inverse of upsampling (Lecture 22-2, pages 58-59)

**Chapter 4: Quantization & CD Specs**
- Reduce precision: 24-bit → 16-bit
- Show SNR: 16-bit gives ~96 dB SNR (from Lecture 22-2, page 11: 20 dB SNR \approx 6 dB per bit → 16×6 = 96 dB)
- Note: Human hearing dynamic range ~120 dB, but in a single listening session (quiet environment) more like 80-90 dB
- 16-bit is sufficient for CD quality

**Chapter 5: The Complete Pipeline**
- Timeline animation: original signal → anti-aliasing → 176.4 kHz samples → downsampling → 44.1 kHz quantized samples → CD encoding
- Allow user to skip steps and see artifacts (e.g., skip anti-aliasing: hear aliasing; skip quantization: data too large)

**Interactive Features:**
- Slider to vary anti-aliasing filter cutoff; watch spectrum update
- Play/pause button to hear audio at each stage (original → downsampled → quantized → reconstructed)
- Toggle: "Expert Mode" shows filter impulse responses, downsampling factor, DCT for JPEG analogy
- Zoom tools for spectral detail

### Implementation Notes
**Complexity:** High
**Key Algorithms:**
- Anti-aliasing FIR filter: `scipy.signal.firwin(numtaps=512, cutoff=22e3, fs=176.4e3)`
- Downsampling: `scipy.signal.decimate(signal, 4)` or custom polyphase downsampler
- Quantization: uniform quantizer at 16-bit resolution
- FFT analysis: `numpy.fft.rfft()`
- Audio synthesis: `scipy.io.wavfile.write()` for playback
- Phase visualization: animated waterfall spectrogram

**Dependencies:** NumPy, SciPy (signal.firwin, signal.decimate, fft), Plotly, librosa, sounddevice (for playback)

### Extension Ideas
**Beginner:** Compare CD (44.1 kHz, 16-bit stereo) bitrate (1.41 Mbps) with MP3 (128 kbps); discuss compression trade-offs
**Advanced:** Implement MPEG audio layer 3 (MP3) or AAC encoding; show perceptual quantization (bits allocated to frequencies with high auditory importance)
**Real-world:** Design anti-aliasing filter for microphone preamp (analog Butterworth, Chebyshev, or Bessel); compute filter order needed for sharp cutoff while maintaining phase linearity

---

## Summary of Novel Simulations

| Simulation | Lecture | Key Insight | Pedagogical Value |
|-----------|---------|-------------|-------------------|
| **Nyquist Paradox Explorer** | 21 | Samples don't uniquely identify signal above Nyquist | Demystifies sampling theorem; interactive boundary exploration |
| **Quantization & Perceptual Quality** | 22-2 | Error spectrum, not just magnitude, drives perception | Links information theory to human sensory science |
| **Aliasing Frequency Mapper** | 21 | Frequencies "fold" at Nyquist; predict aliases algebraically | Gamified practice; builds frequency domain intuition |
| **FM Bandwidth Evolution** | 24 | Modulation index m controls sideband spread & bandwidth | Bessel functions become concrete; Carson's rule emerges |
| **Dithering Artifact Explorer** | 22-2 | Dither trades noise shaping for perceptual quality | Cross-modal (visual + audio) learning reinforces concepts |
| **CD Audio Pipeline** | 25 | Complete chain from microphone to bits | Integration of sampling, filtering, quantization, downsampling |

All simulations emphasize **visual intuition**, **interactive parameter sweeps**, and **real-time feedback** to transform abstract concepts into lived understanding.
