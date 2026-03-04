# BREAKTHROUGH INTERACTIVE TOOLS: Lectures 14-25
## Signals & Systems Web Textbook — European Engineering Education Conference

---

## Breakthrough Tool 1: **Harmonic Decomposition Sculptor**
### Category: F (Composition) + E (Physical World)
### Why a Reviewer Would Be Impressed
This tool lets students literally BUILD a complex waveform by dragging harmonic sliders in a 3D harmonic-space visualization, hearing the sound change in real-time, while watching it reconstruct in the time domain. The novelty: **simultaneous auditory + visual + kinesthetic feedback** on harmonic composition. No textbook tool does this—students hear their math decisions immediately. The conference reviewer hears them say: "I can hear why the 5th harmonic matters for vowel quality!"

### Inspired By (Visual Cues from Slides)
- Lecture 14-3, sheet 02: Harmonic representations, waveform decomposition
- Lecture 15-2, sheet 02: Orthogonal decomposition breakdown
- Lecture 25, sheet 03: Audio CD structure—"many frequencies → many images"

### What Students DO
1. **Start with a target waveform** (square, sawtooth, triangle, speech vowel, or mystery signal)
2. **Drag harmonic amplitude sliders** (1st through 15th harmonics) in an interactive control panel
3. **Hear the reconstructed signal in real-time** via Web Audio API playback
4. **Watch the frequency domain (magnitude spectrum) update** in the background
5. **See convergence metrics** (RMS error to target, % energy captured)
6. **Challenge mode**: Given a target signal and 10 seconds, match it as closely as possible and submit for scoring

### Full Description
The **Harmonic Decomposition Sculptor** is a multi-sensory interface that makes harmonic synthesis tangible. Unlike Fourier Composer (existing tool), this goes beyond visualization—it adds sound and competition.

**Left Panel (Control Zone):**
- 15 vertical sliders, each representing one harmonic (fundamental through 15th)
- Color-coded: fundamental (teal), odd harmonics (purple), even harmonics (blue)
- Real-time numerical display of amplitude values
- "Reset," "Auto-Fit," "Randomize Target" buttons

**Center Panel (3D Harmonic Space):**
- 3D scatter plot: X-axis = harmonic number, Y-axis = amplitude, Z-axis = phase
- Current slider positions shown as draggable points in 3D space
- Target decomposition overlaid as semi-transparent reference points
- Rotate/zoom with mouse to inspect the harmonic structure

**Right Panel (Time Domain + Spectrogram):**
- Top: Waveform display (blue = reconstructed, red = target)
- Bottom: Frequency spectrum (log scale, magnitude)
- Convergence meter: "You are 87% of the way to matching the target"

**Audio Output:**
- Web Audio API plays reconstructed signal at 44.1 kHz
- Volume capped at -6dB for safety
- Loopable, 2-second window

### Interaction Model
**Drag-based sliders** respond instantly. Each slider drag:
1. Updates harmonic amplitude
2. Triggers audio re-synthesis (debounced 50ms)
3. Recomputes RMS error to target
4. Animates 3D point movement
5. Updates waveform overlay

**Modes:**
- **Guided**: Target waveform locked, students match it
- **Sandbox**: No target, create any waveform
- **Challenge**: 30-second timed match-the-signal race with leaderboard

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────────────────┐
│  HARMONIC DECOMPOSITION SCULPTOR  |  Target: Square Wave   │
├──────────────────┬──────────────────┬──────────────────────┤
│ HARMONIC SLIDERS │  3D SPACE        │  TIME DOMAIN         │
│ ┌──────────────┐ │  ┌────────────┐  │  ┌──────────────┐    │
│ │ 1: ████████  │ │  │    /\      │  │  │ ▔▔▔▔▔▔▔      │    │
│ │ 2: ▌▌▌▌      │ │  │   /  \     │  │  │   ▔▔▔▔▔     │    │
│ │ 3: ████████  │ │  │  (3D dots  │  │  │ ▔▔▔▔▔▔▔      │    │
│ │ 4: ▌         │ │  │   rotate)  │  │  └──────────────┘    │
│ │ ...          │ │  │            │  │  ┌──────────────┐    │
│ │              │ │  └────────────┘  │  │  SPECTRUM    │    │
│ │ Error: 5.2%  │ │  (Overlay target)│  │  ▓▓  ▓  ▓    │    │
│ └──────────────┘ │                   │  │  ▓▓▓▓▓▓▓▓▓▓  │    │
│ [Reset] [AutoFit]│                   │  └──────────────┘    │
└──────────────────┴──────────────────┴──────────────────────┘
Audio: ▶ (looping) | Volume: ━━━━◀●━━━ | Mode: [Guided] [Sandbox] [Challenge]
```

### Key "Aha Moments"
- **"Why does the 5th harmonic make that scratchy sound?"** → Hearing and seeing simultaneously
- **"Even though I only changed one slider, the whole waveform shifted!"** → Nonlinear interaction of harmonics
- **"I can match speech, but not music"** → Complexity varies by signal class
- **Leaderboard moment**: "I beat 47 other students at matching the mystery signal in 8 seconds!"

### Learning Theory Alignment
- **Multisensory Learning**: Visual (spectrum) + Auditory (playback) + Kinesthetic (dragging)
- **Constructivism**: Students build understanding by building waveforms
- **Immediate Feedback**: 50ms latency makes cause-effect obvious
- **Intrinsic Motivation**: Challenge mode gamifies learning without being frivolous

### Technical Architecture
**Backend:**
- Harmonic decomposition simulator: numpy FFT of target signal
- Error computation: RMS and SNR metrics
- Leaderboard: store top 100 scores per signal per day

**Frontend:**
- Three.js for 3D harmonic space (draggable points)
- Plotly for 2D waveform + spectrum
- Web Audio API for real-time synthesis (Fourier sum of sine waves)
- Debounced parameter updates (50ms)

### Novelty Claim
**NEVER DONE in S&S education**: Real-time auditory + visual + kinesthetic harmonic composition with challenge scoring and instant feedback. Most tools show harmonics; this tool lets students hear what they're building.

---

## Breakthrough Tool 2: **Fourier Transform Crystallographer**
### Category: E (Physical World) + D (Translation)
### Why a Reviewer Would Be Impressed
This tool shows that the Fourier transform is not just a mathematical abstraction—it's the backbone of X-ray crystallography, MRI imaging, and diffraction optics. Students use a 2D spatial image or crystal structure, apply Fourier transform, see the frequency domain (diffraction pattern), then *reconstruct* the image with missing frequencies to understand resolution limits. The reviewer perspective: "Students learn that Fourier theory solves REAL physics problems—not just exercises."

### Inspired By (Visual Cues from Slides)
- Lecture 20, sheet 03: Fourier transforms in physics—crystallography
- Lecture 20, sheet 06: Diffraction patterns
- Lecture 22, sheet 03: Quantizing images (discretization)
- Lecture 22, sheet 07, 11: Progressive refinement with Roberts' method

### What Students DO
1. **Load or upload a 2D image** (crystal structure, brick wall, face, artifact)
2. **Compute 2D Fourier transform** → see the diffraction pattern (magnitude spectrum in polar form)
3. **Mask frequency components** (erase high-frequency terms, radial bands, angular sectors) to simulate resolution limits
4. **Inverse transform** and compare reconstructed image to original
5. **Experiment with diffraction angle masks** to understand how different spatial frequencies create detail
6. **Challenge**: Given a blurry image and a diffraction pattern, restore the missing frequencies

### Full Description
The **Fourier Transform Crystallographer** bridges pure math to real-world imaging. It answers: "Why does X-ray crystallography work? What does a diffraction pattern tell us?"

**Top-Left Panel (Image Gallery + Upload):**
- Pre-loaded: crystal lattice, brick wall, face, periodic pattern
- Upload button for custom images
- Zoom/pan controls for detail inspection

**Top-Center Panel (2D Fourier Transform):**
- Shows magnitude spectrum in polar coordinates (log scale for visibility)
- Bright spots = strong frequencies, dark = weak
- Interactive crosshair and frequency readout
- Overlay: rings (radial frequency bands), wedges (angular bands)

**Top-Right Panel (Reconstructed Image):**
- Shows image reconstructed from unmasked frequencies
- Side-by-side comparison: Original vs. Reconstructed
- Difference map: where reconstruction fails (red = error)

**Bottom Panel (Mask Controls):**
- **Radial Slider**: "Keep frequencies up to 30% of max" (controls spatial scale)
- **Angular Sector**: Rotate and resize a wedge to keep only certain orientations
- **Notch Filters**: Remove specific frequency bands (to simulate noise or defects)
- **Symmetry Toggle**: Enforce crystallographic symmetry (4-fold, 6-fold)
- Reconstruction metric: "Resolution: 2.4 Ångströms" (if treating as crystal data)

### Interaction Model
**Interactive frequency masking:**
- Click on diffraction pattern → frequency readout
- Drag **Radial Ring** inward/outward → real-time reconstruction
- Drag **Angular Wedge** → rotate and resize to keep only certain directions
- Toggle **"Enforce Symmetry"** → duplicate masked region to symmetry-related positions
- Slider: **"Noise Level"** → adds random phase noise to simulate real experimental data

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────────────────┐
│  FOURIER TRANSFORM CRYSTALLOGRAPHER                         │
├───────────────┬───────────────────────┬───────────────────┤
│ IMAGE         │ FOURIER TRANSFORM     │ RECONSTRUCTED     │
│ ┌───────────┐ │ ┌─────────────────┐   │ ┌───────────────┐ │
│ │ ████████  │ │ │       ⊕         │   │ │ ████████      │ │
│ │ ████████  │ │ │    ◐   ◑    ◐   │   │ │ ████████      │ │
│ │ ████████  │ │ │  ⊕           ⊕   │   │ │ ████████      │ │
│ │ ██░░░██  │ │ │    ◑   ◉    ◑   │   │ │ ██░░░██      │ │
│ │ ████████  │ │ │       ⊕         │   │ │ ████████      │ │
│ └───────────┘ │ └─────────────────┘   │ └───────────────┘ │
│ [Load] [+]    │ Radial: [─────●────] │ Error: 12.3%      │
├───────────────┴───────────────────────┴───────────────────┤
│ MASK CONTROLS                                              │
│ Radial Mask:  [◀──────●──────▶] 30% of max frequency      │
│ Angular:      [◀─────●─────▶]  120° wedge                 │
│ Symmetry:     [6-fold ▼] Enforce ☑                        │
│ Noise:        [◀────●────▶]  5%                           │
└──────────────────────────────────────────────────────────────┘
Real-time metric: Resolution = 2.4 Å | Phase Error = 8.7° | Completeness = 87%
```

### Key "Aha Moments"
- **"The diffraction pattern repeats because the crystal is periodic!"** → Symmetry ↔ Fourier domain
- **"When I cut off high frequencies, fine details disappear!"** → Resolution trade-off
- **"The diffraction spots are where the atomic planes scatter light!"** → Physics of Bragg diffraction
- **"I can reconstruct most of the image from just 30% of the frequencies!"** → Data compression insight

### Learning Theory Alignment
- **Situated Learning**: Math is embedded in real X-ray crystallography / MRI / diffraction
- **Visualization**: 2D → Fourier domain → 2D reconstruction makes transformation reversible
- **Discovery**: Students infer why crystallographers care about high-resolution data
- **Transfer**: Insights apply to image compression, medical imaging, optical design

### Technical Architecture
**Backend:**
- 2D FFT (scipy.fft.fft2) on uploaded image
- Mask application (radial bands, angular wedges, symmetry replication)
- 2D inverse FFT (scipy.fft.ifft2)
- Error metrics: RMSE, structural similarity (SSIM)

**Frontend:**
- Canvas or Three.js for 2D image display
- Plotly heatmap for diffraction pattern (log magnitude)
- Interactive SVG overlays for radial/angular masks
- Real-time reconstruction on mask change

### Novelty Claim
**NEVER DONE in S&S education**: Interactive 2D Fourier transform with masking and reconstruction showing why real-world imaging (X-ray, MRI, diffraction) works. Most tools only show 1D signals; this reveals the spatial structure of frequency domain.

---

## Breakthrough Tool 3: **Sampling Alias Detector Game**
### Category: G (Competition) + A (Reverse Engineering)
### Why a Reviewer Would Be Impressed
Students are shown a *discrete signal* and must infer: (1) the original continuous signal, (2) the sampling rate, and (3) whether aliasing occurred. They make a prediction, then the tool shows them the actual spectrum and lets them adjust their answer in real-time. The gamification: speedrun mode with difficulty levels. Reviewers see: "Students are debugging the most common Signals & Systems mistake—aliasing—as a playable challenge."

### Inspired By (Visual Cues from Slides)
- Lecture 21, sheet 03, 06, 09: Aliasing—the effect of sampling (input frequency vs. output frequency)
- Lecture 21, sheet 09: Anti-aliasing filter + reconstruction
- Lecture 25, sheet 09: CD quality—anti-aliasing filter mention

### What Students DO
1. **See a discrete-time signal** (plot of sample values at integer indices)
2. **Predict the original analog frequency, sampling rate, and whether aliasing occurred**
3. **Submit guess** → system reveals true spectrum, sampling rate, and original signal
4. **Adjust parameters (Nyquist frequency, bandpass filter cutoff)** to fix alias
5. **Score points** for correct diagnosis, speed, and confidence
6. **Compete on leaderboard** for fastest alias detection

### Full Description
The **Sampling Alias Detector Game** turns aliasing from a theoretical hazard into a playable detective story. Students see a sampled signal and must work backward to infer what was lost.

**Left Panel (Given Signal):**
- Discrete-time signal x[n] plotted as stem plot
- Sample period T shown
- Button: "Reveal True Frequency?" (starts timer for points)

**Center Panel (Prediction Input):**
- **Continuous Signal Estimator:**
  - Slider: "Original frequency (Hz)" [0 to 50 kHz]
  - Readout: Nyquist frequency = F_s / 2
  - Indicator: "RED = above Nyquist (ALIASED!)" or "GREEN = within Nyquist"
- **Sampling Rate Estimator:**
  - Slider: "Sampling frequency (Hz)" [1 kHz to 100 kHz]
- **Aliasing Diagnosis:**
  - Radio button: "No aliasing" / "Aliased from higher freq" / "Aliased from negative freq"
  - If aliased: text input "True frequency was ___ Hz (alias of this)"

**Right Panel (Reveal & Compare):**
- **True Spectrum**: Magnitude spectrum of the underlying continuous signal (before sampling)
- **Sampled Spectrum**: DT frequency response (periodic in normalized frequency)
- **Overlay**: Student's prediction overlaid in dashed lines
- **Score**: Points for accuracy, speed bonus if correct in <20 seconds
- **Feedback**: "You diagnosed the alias correctly! True signal was 18 kHz, aliased to 2 kHz at 20 kHz sampling."

### Interaction Model
**Prediction → Reveal → Adjust loop:**
1. Student adjusts sliders
2. Clicks "Submit Prediction"
3. Timer stops, score computed
4. True spectrum appears with student prediction overlaid
5. Student can adjust sliders and re-submit (for learning, no additional points)
6. "Next Challenge" button loads new problem

**Difficulty Levels:**
- **Easy**: Low frequencies, obvious aliasing
- **Medium**: Moderate frequencies, subtle aliasing or no aliasing
- **Hard**: High frequencies, multiple possible aliases, noise-like signals
- **Expert**: Phase-aliased signals (same magnitude as original, but shifted phase)

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────────────┐
│  SAMPLING ALIAS DETECTOR GAME  | Difficulty: MEDIUM     │
├──────────────┬─────────────────┬──────────────────────┤
│ GIVEN SIGNAL │ YOUR PREDICTION │ TRUE SPECTRUM        │
│ ┌──────────┐ │ ┌─────────────┐ │ ┌────────────────┐  │
│ │     •    │ │ │ Freq: ━●─── │ │ │    ▓ ▓      ▓  │  │
│ │   •   •  │ │ │ Nyquist:10kHz│ │ │  ▓ ▓ ▓    ▓ ▓  │  │
│ │ •     •  │ │ │ F_s: ━─●──── │ │ │ ▓▓▓▓▓▓▓  ▓▓▓▓  │  │
│ │ •     •  │ │ │ Aliased? [○] │ │ │                  │  │
│ │   •   •  │ │ │ True: ___Hz  │ │ │ (Dashed overlay: │  │
│ │     •    │ │ │              │ │ │  your prediction)│  │
│ └──────────┘ │ │ [Submit]     │ │ └────────────────┘  │
│ T = 50 µs    │ └─────────────┘ │ Score: 850 pts      │
│ n = 0..19    │                  │ Speed bonus: +100   │
└──────────────┴─────────────────┴──────────────────────┘
Leaderboard: 1. Sarah (12,340 pts) | 2. Alex (11,890) | 3. You (10,550)
[Easy] [Medium] [Hard] [Expert] | Time: 18.3 s | [Next Challenge]
```

### Key "Aha Moments"
- **"Oh! The 18 kHz signal looks like 2 kHz because the sampling rate aliased it!"** → Aliasing as modulo arithmetic
- **"If I raise the sampling rate, the alias disappears!"** → Nyquist frequency fixes aliasing
- **"I can't tell from the samples alone if it was 2 kHz or 18 kHz!"** → Fundamental ambiguity in sampling
- **Speedrun**: "I diagnosed that as an alias in 7 seconds—faster than anyone today!"

### Learning Theory Alignment
- **Gamification**: Points, leaderboard, difficulty levels sustain engagement
- **Misconception Correction**: Students directly confront aliasing (the #1 pitfall in sampling)
- **Rapid Feedback**: Wrong answer immediately visible in spectral overlay
- **Transfer**: Insights apply to audio DSP, medical imaging, control systems

### Technical Architecture
**Backend:**
- Database of pre-computed challenges (signal + sampling rate pairs covering aliasing cases)
- DT FFT of sampled signals
- Score computation: distance between student guess and true parameters
- Leaderboard: Redis cache with daily/weekly/all-time rankings

**Frontend:**
- Plotly stem plots for DT signals
- Plotly bar charts for magnitude spectra
- Interactive sliders with validation (Nyquist indicator)
- Timer with score calculation on submit

### Novelty Claim
**NEVER DONE in S&S education**: Gamified alias detection with real-time feedback, leaderboard, and difficulty progression. Makes the most dangerous Signals & Systems mistake (aliasing) into a competitive, engaging challenge rather than a theory problem.

---

## Breakthrough Tool 4: **Modulation Radar Constructor**
### Category: F (Composition) + E (Physical World)
### Why a Reviewer Would Be Impressed
Students design an AM/FM radar signal by choosing modulation type, carrier frequency, and modulation parameters. They see the time-domain signal, frequency spectrum, and a simulated **radar target response**. Then they adjust parameters to maximize target detection and minimize interference. It's a *design challenge* rooted in real electrical engineering (radar systems, communications). Reviewers think: "This is how actual engineers design modulation schemes—students are solving a real problem."

### Inspired By (Visual Cues from Slides)
- Lecture 23, sheet 03: Amplitude modulation (AM) with carrier
- Lecture 23, sheet 05: Synchronous demodulation, improper radio receiver
- Lecture 24, sheet 03, 06, 09: Phase/frequency modulation (PM/FM)
- Lecture 25, sheet 09: Tracking with feedback control

### What Students DO
1. **Choose modulation scheme**: AM, DSB-SC (double sideband suppressed carrier), FM, or hybrid
2. **Set parameters**:
   - Carrier frequency (100 kHz to 10 GHz)
   - Modulation frequency (audio, 100 Hz to 10 kHz)
   - Modulation index (depth for AM, deviation for FM)
3. **Visualize the modulated signal** (time domain + frequency domain)
4. **Add a simulated target**: radar bounce from object at distance D, velocity V
5. **Adjust parameters to maximize Doppler detectability** while avoiding interference bands
6. **Challenge**: "Design a radar signal that distinguishes a 50 mph car from a 30 mph truck"

### Full Description
The **Modulation Radar Constructor** shows that modulation is not just math—it's the key to communicating through noisy channels and detecting moving objects.

**Top-Left Panel (Modulation Designer):**
- **Signal Type**: [AM] [DSB-SC] [FM] [Multi-tone]
- **Carrier Frequency**: Slider or text [100 kHz to 10 GHz]
- **Modulation Source**:
  - Simple tone: slider "Frequency [100 Hz–10 kHz]"
  - Complex: upload audio file or select preset speech/music
- **Modulation Depth** (AM): Slider [0% to 100%] (overmodulation warning at >100%)
- **Frequency Deviation** (FM): Slider [0 to 200 kHz]
- **Carson's Bandwidth** readout: Auto-computed and displayed

**Top-Right Panel (Time Domain + Frequency Domain):**
- Dual plot:
  - Top: Time-domain signal (blue), overlaid modulating signal (red dashed)
  - Bottom: Magnitude spectrum (log scale), side bands highlighted
- Zoom to first 5 cycles or first 1 ms for detail
- Frequency axis markers for carrier ±sidebands

**Middle Panel (Radar Target Simulation):**
- **Target Selector:**
  - Distance: Slider [0 to 10 km] → delay in received signal
  - Velocity: Slider [-100 to +100 mph] → Doppler shift
  - RCS (Radar Cross Section): Slider [tiny to large] → attenuation
- **Received Signal**:
  - Plot showing transmitted signal + received (delayed, Doppler-shifted, attenuated)
  - Overlap visualization
- **Detection Metric**: "SNR = 18.3 dB | Doppler shift = 1.2 kHz | Detectability = GOOD"

**Bottom Panel (Demodulation & Interference Analysis):**
- **Receiver Type**: [Envelope detector (AM)] [Synchronous demod (AM/DSB)] [FM discriminator] [Doppler filter]
- **Demodulated Output**: Plot of extracted signal (target velocity/range)
- **Interference Bands**: Red zones showing frequencies where atmospheric noise or other radars jam the signal
- **Design Score**: "Signal robust in interference? 78/100 | Doppler separation? 92/100"

### Interaction Model
**Real-time parameter update:**
1. Adjust any slider → time domain and spectrum refresh instantly
2. Receiver automatically recomputes for current parameters
3. Doppler shift calculated and displayed
4. Detection metric updates
5. Interference zones shown in red (student avoids these frequencies)

**Presets:**
- NATO AM Broadcast (535–1605 kHz)
- Aircraft radar (10 GHz)
- Police radar (X-band, 10.5 GHz)
- Cell phone (carrier 900 MHz to 2.6 GHz)
- Audio modem (1.2 kHz to 2.4 kHz FSK)

**Challenge Mode:**
- Scenario: "A 50 mph car is 5 km away. A 30 mph truck is 4.8 km away. Design a radar that distinguishes them."
- Student adjusts carrier, modulation, and demodulator type
- Scoring: Detection probability for each target, false-alarm rate
- Leaderboard: Most robust signal design

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────────────┐
│  MODULATION RADAR CONSTRUCTOR  | Challenge: Dual Target │
├──────────────┬────────────────┬───────────────────────┤
│ MODULATOR    │ TIME + FREQ    │ TARGET SETUP          │
│ Type: [FM▼]  │ ┌────────────┐ │ Distance: ━●─ 5.0 km │
│ Carrier:     │ │ ▓▓▓▓▓▓▓▓▓  │ │ Velocity: ─●─ 50 mph │
│ ━●─ 10.5 GHz │ │ ▓▓▓▓▓▓▓▓▓  │ │ RCS: ───●─ medium    │
│ Modulation:  │ │ ▓▓▓▓▓▓▓▓▓  │ │ Target 2:            │
│ ━─●──────    │ │ [Freq view] │ │ Dist: ━──● 4.8 km    │
│ 1.2 kHz      │ │ ▓ ▓   ▓ ▓   │ │ Vel: ──●─ 30 mph     │
│ Deviation:   │ │           │ │ Doppler₁: +1.2 kHz   │
│ ━────●─      │ └────────────┘ │ Doppler₂: +0.72 kHz  │
│ 100 kHz      │ Carson BW=202kHz│ Separation: 480 Hz   │
│ Carson BW:   │                 │ (GOOD)               │
│ 202 kHz      │                 └───────────────────────┘
├──────────────┴────────────────┴───────────────────────┤
│ RECEIVER: [Doppler Filter ▼]                           │
│ Output Range: 0–5 km | Output Velocity: 0–100 mph    │
│ Interference Zones: [████████] 10.502–10.504 GHz (RED)│
│ SNR: 21.4 dB | Detection: CAR (98%) + TRUCK (89%)     │
└──────────────────────────────────────────────────────────┘
[Easy: Static target] [Medium: One moving target] [Hard: Dual target] | Score: 156/200
```

### Key "Aha Moments"
- **"FM gives me better range resolution than AM!"** → Why police use FM radar
- **"The Doppler shift tells me the car's speed, not the carrier frequency!"** → Demodulation extracts information
- **"I need wider bandwidth to detect faster speeds!"** → Carson's rule
- **"Interference zones are where other systems operate—I must avoid them!"** → Spectrum coexistence constraint
- **Challenge solved**: "I separated the car from the truck using FM with a 100 kHz deviation!"

### Learning Theory Alignment
- **Authentic Problem**: Real radar design, not abstract modulation exercises
- **Design Thinking**: Parameters constrained by physics (Carson's BW, Nyquist for targets)
- **Feedback Loop**: Parameter change → instant signal update → new detection metric
- **Transfer**: Insights apply to wireless communications (LTE, WiFi, cellular)

### Technical Architecture
**Backend:**
- Modulated signal synthesis: numpy signal generation (AM/FM/SSB)
- Doppler shift calculation: frequency scaling
- Radar echo simulation: delayed + attenuated copy with Doppler
- Demodulation: envelope detection, synchronous mixing, discriminator circuits
- Interference band database

**Frontend:**
- Plotly for time-domain and spectrum plots
- Dual-axis plot: time and frequency
- Interactive sliders with real-time updates (debounced 100ms)
- SVG overlay for interference zones (red bands)

### Novelty Claim
**NEVER DONE in S&S education**: Interactive radar design tool where students adjust modulation type, carrier, and demodulation to detect multiple moving targets. Combines modulation theory, Doppler physics, and real-world constraints (interference, bandwidth).

---

## Breakthrough Tool 5: **Phase-Frequency Domain Navigator**
### Category: D (Translation) + F (Composition)
### Why a Reviewer Would Be Impressed
Most tools show magnitude spectrum OR phase spectrum. This tool shows **both simultaneously** in a unified 3D interactive space: frequency on X-axis, magnitude on Y-axis, phase on Z-axis (or color). Students rotate the 3D plot, click on frequency components, and see how changing phase shifts the time-domain signal. The insight: "Phase is not optional—it's as important as magnitude." Reviewers see a completely novel visualization never done before in S&S teaching.

### Inspired By (Visual Cues from Slides)
- Lecture 18-2, sheet 03, 06: Effects of phase on DT signals
- Lecture 19-2, sheet 03: Phase/frequency modulation
- Lecture 16-2, sheet 05: Fourier transform showing magnitude and phase separately

### What Students DO
1. **Load or construct a signal** (step, impulse, speech, image, custom)
2. **Compute Fourier transform** → extract magnitude and phase
3. **Explore in 3D phase-magnitude space:**
   - Rotate the 3D plot to see magnitude profile
   - Tilt to see phase profile
   - Zoom in on specific frequencies
4. **Modify phase at individual frequencies** → watch time-domain signal change
5. **Challenge**: "Reconstruct the original signal given only its magnitude; match a target signal by adjusting phase"

### Full Description
The **Phase-Frequency Domain Navigator** reveals the hidden importance of phase. It answers: "Why does phase matter? Why can't I just use magnitude?"

**Left Panel (3D Phase-Magnitude Space):**
- 3D scatter plot or surface:
  - X-axis: Frequency (0 to 2π for DT, or 0 to F_s for CT)
  - Y-axis: Magnitude |X(f)|
  - Z-axis or Color: Phase ∠X(f) (colored from -π to +π, red to blue gradient)
- Interactive rotation, zoom, pan with mouse
- Hover over point → shows (frequency, magnitude, phase) tooltip
- Click on point → displays that component in isolation

**Top-Right Panel (3D Controls):**
- **View presets**: [Magnitude-only] [Phase-only] [Both (3D)] [Phase heatmap]
- **Rotation buttons**: "Auto-rotate" toggle
- **Zoom slider**
- **Component highlighting**: Select a range of frequencies to highlight in yellow
- **Symmetry toggle** (for real signals, phase is antisymmetric)

**Middle-Right Panel (Time-Domain Signal):**
- Plot of x[n] or x(t)
- Synchronized with 3D plot: if you select a frequency component, its contribution to x[n] is highlighted
- "Magnitude-only reconstruction" button: shows what signal looks like if phase is zeroed
- "Phase-only reconstruction" button: shows what signal looks like if magnitude is flat

**Bottom Panel (Phase Adjuster):**
- **Frequency Slider**: "Select frequency: ━●─ 50 Hz"
- **Phase Rotator**: Circular dial or slider [−π to +π]
- **Magnitude Slider** (locked by default, but unlockable): Modify component magnitude
- **Preview**: As you adjust, live update of time-domain signal
- "Undo" button to revert to original

### Interaction Model
**3D exploration → phase tweaking → time-domain feedback:**
1. Rotate 3D plot freely with mouse
2. Click on frequency component → rotator dial appears for that frequency
3. Drag phase dial → time-domain signal updates in real-time
4. Double-click on component → locks to that frequency for fine adjustment
5. "Reset phase" button → revert to original phase at that frequency

**Synchronization:**
- 3D plot shows current state of all phases
- Whenever time-domain signal changes (due to phase adjustment), 3D plot updates
- Phase heatmap view shows phase as color map (purple = −π, blue = 0, red = +π)

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────────────┐
│  PHASE-FREQUENCY DOMAIN NAVIGATOR                       │
├──────────────────┬──────────────────┬─────────────────┤
│ 3D SPACE         │ TIME DOMAIN      │ CONTROLS        │
│ ┌──────────────┐ │ ┌───────────┐   │ Freq: ━●─       │
│ │     /\       │ │ │ ▄▄▄▄▄▄▄   │   │ Phase: ⊗       │
│ │    /  \      │ │ │ ▄▄▄▄▄▄▄   │   │ [-π, +π]      │
│ │   /    \     │ │ │▄▄▄▄▄▄▄▄▄  │   │          ◀─●─▶ │
│ │  (mag blue)  │ │ │ ▄▄▄▄▄▄▄▄   │   │ [Reset]      │
│ │  (phase red) │ │ │ ▄▄▄▄▄▄▄   │   │              │
│ │ [Rotate]     │ │ └───────────┘   │ View: [3D]    │
│ └──────────────┘ │ Reconstruction  │ [Mag] [Phase] │
│ (rotate freely)  │ from selected    │ [Heatmap]     │
│                  │ frequencies      │ [Auto-rotate] │
└──────────────────┴──────────────────┴─────────────────┘
Legend: Blue=0°phase, Red=180°, Purple=-180° | Signal: speech | Mode: [Explore] [Challenge]
```

### Key "Aha Moments"
- **"If I change the phase of just one component, the entire waveform shifts in time!"** → Phase encodes timing
- **"The magnitude alone looks like white noise when I zero all phases!"** → Phase carries structure
- **"Delaying the signal just rotates all phases uniformly!"** → Delay = linear phase
- **"I can reconstruct most of the signal from just magnitude if I guess the phase!"** → Phase reconstruction challenge

### Learning Theory Alignment
- **Visualization**: 3D simultaneous display of magnitude + phase
- **Embodied Cognition**: Rotating the 3D plot makes abstract frequency domain tangible
- **Misconception Correction**: Students discover phase is not secondary to magnitude
- **Transfer**: Phase concepts apply to filtering (phase distortion), modulation (phase modulation)

### Technical Architecture
**Backend:**
- FFT to get magnitude and phase
- Phase adjustment: multiply by e^(jΔφ) at selected frequency
- Inverse FFT for updated time-domain signal
- Symmetry enforcement for real signals

**Frontend:**
- Three.js for 3D plot (scatter or surface)
- Plotly for 2D time-domain plot (synchronized with 3D)
- SVG for phase rotator dial
- Real-time update on mouse interaction (WebGL for 3D performance)

### Novelty Claim
**NEVER DONE in S&S education**: Interactive 3D simultaneous magnitude + phase visualization with real-time phase adjustment and time-domain feedback. Reveals phase as a fundamental signal property, not a footnote.

---

## Breakthrough Tool 6: **Quantization Forensics Lab**
### Category: A (Reverse Engineering) + E (Physical World)
### Why a Reviewer Would Be Impressed
Given an image or audio signal that has been quantized to N bits, students must infer: (1) how many bits were used, (2) what quantization method (linear, logarithmic, dithered), (3) where quantization artifacts appear. They compare the quantized signal to the original, measure SNR, and solve challenges like "Restore a 4-bit image to near-CD quality using dithering." Real-world connection: CDs, JPEGs, MP3s all use quantization. Reviewers see: "Students debug quantization as forensics, not theory."

### Inspired By (Visual Cues from Slides)
- Lecture 22, sheet 03: Quantization, discrete amplitudes
- Lecture 22, sheet 07, 11: Quantizing images with Roberts' method
- Lecture 25, sheet 03: CD structure — quantization, sampling, filtering

### What Students DO
1. **Load a quantized signal** (audio or image, N bits unknown)
2. **Guess the bit depth** [4, 8, 12, 16, 24 bits]
3. **Choose quantization method**: [Uniform] [Logarithmic (µ-law)] [Dithered]
4. **Inspect for artifacts**: Visible contour bands in images, buzzing in audio
5. **Compare to original**: See difference image (error heat map)
6. **Challenge**: "Restore a 4-bit image using dithering; match original SNR ≥ 40 dB"

### Full Description
The **Quantization Forensics Lab** teaches students that quantization is not a minor effect—it's a major design trade-off in audio/image systems.

**Top-Left Panel (Signal Selector):**
- **Signal Library:**
  - Pre-loaded audio: speech, music, Handel's Messiah (real CD example)
  - Pre-loaded images: face, brick wall, grayscale photo, 8-bit image
  - Upload custom audio or image
- **Sample Viewer**: Waveform (audio) or image (image) at full precision

**Top-Right Panel (Forensics Analysis):**
- **Histogram of amplitude values**: Student guesses bit depth from spikes
- **Autocorrelation of errors**: Dithering vs. non-dithered error pattern
- **Spectral analysis of error**: Dithering spreads error across frequencies
- Readouts: "This signal has _____ discrete levels detected" (student fills in guess)

**Middle Panel (Reconstruction Attempts):**
- **Slider 1: Bit Depth** [4 to 24 bits]
- **Slider 2: Quantization Type** [Uniform] [µ-law] [A-law] [Dithered uniform]
- **Dithering Strength** (if dithered): [None] [TPDF (Triangular PDF)] [Noise-shaped]
- **Preview**: Reconstructed signal shown in overlay (student adjusts to match original)

**Bottom Panel (Error Analysis):**
- **SNR Meter**: Shows SNR vs. original (goal: match original SNR)
- **PESQ score** (for audio): Perceptual quality metric
- **SSIM score** (for images): Structural similarity to original
- **Artifact detection**: "Contour bands detected at N levels" or "None"
- **Correct answer reveal**: "Correct! This was a 16-bit uniform quantization. SNR = 96 dB."

### Interaction Model
**Guess → Compare → Adjust loop:**
1. Student adjusts bit depth and quantization type sliders
2. Reconstruction updates in real-time
3. Error heat map appears (red = large error, blue = small error)
4. SNR metric updates
5. Student submits answer or keeps adjusting
6. On submit, correct parameters revealed with detailed feedback

**Audio playback option:**
- Button: "Listen to original" (high fidelity)
- Button: "Listen to quantized" (student's guess)
- Difference is audible for low bit depths (4–8 bits very noisy; 16+ nearly imperceptible)

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────────┐
│  QUANTIZATION FORENSICS LAB                          │
├───────────────┬──────────────────┬─────────────────┤
│ SIGNAL        │ HISTOGRAM        │ ERROR ANALYSIS  │
│ ┌───────────┐ │ ┌──────────────┐ │ SNR: 42.3 dB   │
│ │ ▄▄▄▄▄▄▄▄▄ │ │ ▒▒▒▒▒  ▒▒▒▒▒ │ │ PESQ: 3.2/5    │
│ │ ▄▄▄▄▄▄▄▄▄ │ │ ▒▒▒▒▒▒▒▒▒▒▒▒▒ │ │ Artifacts: YES │
│ │▄▄▄▄▄▄▄▄▄▄▄ │ │ ▒▒▒▒▒▒▒▒▒▒▒▒▒ │ │ (contour bands)│
│ │ ▄▄▄▄▄▄▄▄▄ │ │ ▒▒▒▒▒▒▒▒▒▒▒▒▒ │ │ Dithering:     │
│ │ ▄▄▄▄▄▄▄▄▄ │ │ ▒▒▒▒▒  ▒▒▒▒▒ │ │ ☑ Recommended │
│ └───────────┘ │ └──────────────┘ │                │
│ (original)    │ 256 levels       │ Error map:     │
│               │ detected         │ [█████████]    │
├───────────────┴──────────────────┴─────────────────┤
│ RECONSTRUCTION SETUP                                │
│ Bit Depth: [4 ▼]   Quantization: [Uniform ▼]       │
│ [4] [8] [12] [16] [24]  |  Dithering: [TPDF ▼]    │
│ ━●─────  (approx 16 levels) | [None] [TPDF] [NS]  │
│ [▶ Listen Original] [▶ Listen Quantized] [Compare] │
└─────────────────────────────────────────────────────┘
Challenge: Match SNR ≥ 40 dB with ≤ 8 bits | Your attempt: 7.1 dB | [Submit] | Mode: [Forensics] [Challenge]
```

### Key "Aha Moments"
- **"I can see the banding in this 4-bit image, but with dithering it looks much smoother!"** → Dithering trades noise for spatial detail
- **"The quantization error is not random—it's structured!"** → Why dithering matters
- **"CD audio is 16-bit, but my forensic analysis detected only 65,536 levels, not 16 million!"** → Bit depth is real and measurable
- **"Audio at 8 bits sounds terrible, but 16 bits is transparent!"** → Psychoacoustics + bit depth

### Learning Theory Alignment
- **Forensic Analysis**: Students become "quantization detectives," finding evidence in histograms and error patterns
- **Trade-off Discovery**: Low bits = fewer levels but smaller file; dithering = noise but better perceptual quality
- **Authentic Task**: Real audio/image systems use these decisions
- **Multi-modal**: Visual (histogram, heat map) + Auditory (playback) feedback

### Technical Architecture
**Backend:**
- Quantization simulator: uniform, logarithmic (µ-law), dithered quantization
- SNR computation: 10 * log10(signal_power / error_power)
- PESQ and SSIM libraries (scipy, skimage)
- Histogram and autocorrelation of quantization error
- Artifact detection: curvature analysis for contour bands

**Frontend:**
- Plotly for waveform, histogram, spectrogram
- Canvas or WebGL for image quantization visualization
- Web Audio API for playback (decode audio, apply quantization, play)
- Heat map overlay for error visualization

### Novelty Claim
**NEVER DONE in S&S education**: Interactive quantization forensics where students reverse-engineer bit depth and method, then use dithering to improve quality. Combines signal processing, perceptual science, and real-world audio/image design.

---

## Breakthrough Tool 7: **Filter Design Showdown**
### Category: F (Composition) + G (Competition)
### Why a Reviewer Would Be Impressed
Students design a digital or analog filter to meet specifications (passband ripple, stopband attenuation, transition width, group delay). They can choose filter type (Butterworth, Chebyshev, elliptic) and order. They see the pole-zero map, magnitude response, and phase response update in real-time. Then they compete: "Who can design the lowest-order filter meeting the spec?" with a leaderboard. The innovation: interactive pole placement with instant feedback on all metrics. Reviewers see: "This is how real engineers design filters—not by hand-calculating coefficients."

### Inspired By (Visual Cues from Slides)
- Lecture 14-3, sheet 08: Lowpass filtering, RC circuit
- Lecture 16-2, sheet 03, 05: Fourier transform, moments
- Lecture 20, sheet 03, 06: Filtering example—electrocardiogram

### What Students DO
1. **Choose filter type**: [Butterworth] [Chebyshev I/II] [Elliptic] [Custom]
2. **Set specifications:**
   - Passband frequency: 0–2 kHz (slider)
   - Passband ripple: 0–3 dB
   - Stopband frequency: 3–10 kHz (slider)
   - Stopband attenuation: 20–100 dB (slider)
3. **Adjust filter order** (slider) and see pole-zero map update
4. **View results:**
   - Magnitude response (dB)
   - Phase response (degrees)
   - Group delay
   - Number of poles/zeros
5. **Test on benchmark signals** (white noise, chirp, speech) and compare output SNR
6. **Challenge**: Design the lowest-order filter meeting specs; submit for leaderboard scoring

### Full Description
The **Filter Design Showdown** teaches students that filter design is a multi-objective optimization problem: meet specs with minimum complexity (order).

**Top-Left Panel (Specification Sliders):**
- **Passband Cutoff**: ━●─ 2.0 kHz
- **Passband Ripple**: ━●─ 0.5 dB (only for Chebyshev I)
- **Stopband Cutoff**: ━●─ 5.0 kHz
- **Stopband Attenuation**: ━●─ 40 dB
- **Filter Type**: [Butterworth] [Chebyshev I] [Chebyshev II] [Elliptic] [Custom]
- **Order**: ━●─ 5 (auto-incrementing if spec not met)
- **Metric**: "Order 5 Butterworth | Meets all specs: YES"

**Top-Right Panel (Pole-Zero Map):**
- Complex plane (real on X, imaginary on Y)
- Poles shown as ✕, zeros as ○
- Unit circle (light gray) for reference
- Interactive: click and drag poles/zeros to manually adjust filter (if in Custom mode)
- Click-to-add/remove pole/zero buttons

**Middle Panel (Magnitude + Phase Response):**
- Dual plot:
  - Top: Magnitude response (dB) on log-log scale, with shaded passband/stopband regions
  - Bottom: Phase response (degrees) or group delay (seconds)
- Vertical dashed lines: passband edge, stopband edge, transition band
- Red shading: regions where spec is violated
- Hover for frequency-specific readout

**Bottom Panel (Filter Performance):**
- **Test Signal**: [White noise] [Chirp sweep] [Speech] [ECG artifact] [Custom]
- **Input Spectrum** (left) and **Output Spectrum** (right), overlaid
- **SNR in passband**: "98.5 dB"
- **Attenuation in stopband**: "−42.3 dB"
- **Impulse response**: Brief stem plot (first 20 samples)

### Interaction Model
**Spec → Design → Test → Score loop:**
1. Student adjusts specification sliders
2. Filter order automatically increases if needed to meet spec
3. Pole-zero map updates (poles move to satisfy Butterworth/Chebyshev equations)
4. Magnitude and phase response update
5. Student tests on benchmark signal, sees attenuation metrics
6. Submits design → scored on order (lower = better)

**Leaderboard:**
- Sorted by minimum order meeting all specs
- Tied designs compared by group delay (lower = better)
- Tied designs compared by design time (faster = better)
- Daily/weekly/all-time rankings

### Multi-Panel Layout
```
┌────────────────────────────────────────────────────┐
│  FILTER DESIGN SHOWDOWN  | Specs: Lowpass, 2kHz   │
├─────────────┬──────────────┬──────────────────────┤
│ SPECS       │ POLE-ZERO    │ MAGNITUDE RESPONSE   │
│ P.Band: 2kHz│ ┌──────────┐ │ ┌──────────────────┐│
│ ━●─ 2.0    │ │   ×   ×  │ │ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ││
│ Ripple: 0.5dB│ │ ○  +  ×  │ │ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ││
│ S.Band: 5kHz│ │   ×   ×  │ │ │ ▓▓▓ ▓▓▓ ▓▓▓ ▓  ││
│ ━●─ 5.0    │ │ × × ○ × × │ │ │ ▓▓ ▓ ▓ ▓ ▓ ▓  ││
│ Atten: 40dB │ │      ◐  │ │ │ ▓▓▓ ▓▓▓ ▓▓▓ ▓  ││
│ ━●────     │ │   ×   ×  │ │ │ ▓ ▓ ▓ ▓ ▓ ▓ ▓  ││
│ Type: [Butter▼]└──────────┘ │ ▓ ▓ ▓ ▓ ▓ ▓ ▓  ││
│ Order: 5   │ Chebyshev    │ └──────────────────┘│
│            │ poles shown  │  Passband | Stopband│
├─────────────┴──────────────┴──────────────────────┤
│ BENCHMARK TEST: Speech Signal                     │
│ Input Spectrum [██████] Output Spectrum [███]     │
│ SNR passband: 98.5 dB | Attenuation: −42.3 dB   │
│ [White Noise] [Chirp] [Speech] [ECG] [Custom▼]   │
└────────────────────────────────────────────────────┘
Leaderboard: 1. Alex (Order 4) | 2. Sarah (Order 5) | 3. You (Order 5, −35 dB phase distortion)
[Submit Design] | Challenge: Meet 100 dB stopband with < 6th order | Status: POSSIBLE
```

### Key "Aha Moments"
- **"Higher order gives steeper transition but more phase distortion!"** → Trade-off between magnitude and phase
- **"Elliptic filters are scarier-looking poles but smaller order than Butterworth!"** → Rational complexity trade-off
- **"I can see the poles moving as I increase the cutoff frequency!"** → Frequency scaling of pole locations
- **"Speech at 5 kHz sounded muffled because I'm filtering too aggressively!"** → Perceptual feedback on design

### Learning Theory Alignment
- **Interactive Design**: Real-time feedback on every parameter change
- **Multi-objective Optimization**: Order vs. passband ripple vs. stopband attenuation
- **Gamification**: Leaderboard drives engagement
- **Transfer**: Same concepts apply to analog circuits, mechanical vibration control, seismic filtering

### Technical Architecture
**Backend:**
- SciPy signal.butter, signal.cheby1, signal.cheby2, signal.elliptic functions
- Pole-zero extraction from transfer function
- Magnitude and phase response via signal.freqs or signal.freqz
- Group delay computation: −d(phase)/d(ω)
- Leaderboard: Redis cache, score = (1000 / order) + phase_penalty

**Frontend:**
- Plotly for magnitude/phase plots
- Three.js or custom Canvas for pole-zero plot (draggable poles in Custom mode)
- Real-time update on slider change (debounced 100ms)
- Web Audio API for listening to filtered signal

### Novelty Claim
**NEVER DONE in S&S education**: Interactive filter design showdown where students adjust specs in real-time, see pole-zero map and frequency response simultaneously, test on multiple signals, and compete for lowest-order design. Combines classical filter theory with modern interactive optimization.

---

## Breakthrough Tool 8: **Discrete-Time Reconstruction Puzzle**
### Category: A (Reverse Engineering) + B (Design Challenge)
### Why a Reviewer Would Be Impressed
Given a discrete-time signal (samples only, no knowledge of original sampling rate or continuous signal), students must infer the original continuous signal and sampling rate. They manipulate reconstruction filters (lowpass cutoff, rolloff steepness) and interpolation methods (zero-order hold, linear, cubic spline, sinc). They see the reconstructed continuous signal and can compare to the true original. It's a detective game: "Find the continuous signal that was sampled." Reviewers see: "This teaches the Nyquist theorem experientially—students discover why sampling rate matters."

### Inspired By (Visual Cues from Slides)
- Lecture 21, sheet 03, 06, 09: Sampling and reconstruction
- Lecture 21, sheet 09: Anti-aliasing filter + reconstruction
- Lecture 25, sheet 09: Reconstruction from DT signal

### What Students DO
1. **Given a discrete-time signal** x[n] (plot of samples only)
2. **Infer the sampling period** T (or equivalently, F_s = 1/T)
3. **Choose reconstruction method:**
   - Zero-order hold (piecewise constant)
   - First-order hold (linear interpolation)
   - Cubic spline interpolation
   - Sinc interpolation (ideal lowpass)
4. **Adjust lowpass reconstruction filter cutoff** (slider: 0.1 F_s to 0.5 F_s = Nyquist)
5. **Adjust filter rolloff** (steepness, to see ringing artifacts)
6. **View reconstructed continuous signal** and compare to "true" original
7. **Challenge**: "Reconstruct this 8 kHz sampled speech to match original 16 kHz quality"

### Full Description
The **Discrete-Time Reconstruction Puzzle** teaches students that reconstruction is not trivial—it's an art and a science. The same samples can reconstruct to many different continuous signals if the sampling rate is wrong.

**Top-Left Panel (Discrete Signal Viewer):**
- Stem plot of x[n] with index (sample number)
- Assume T = 1 initially; student adjusts T to match intuitive frequency content
- Slider: **"Sample Period T: ━●─ 0.5 ms"** (equivalently F_s = 2 kHz)
- Readout: "Nyquist frequency = 1 kHz"
- Visual indicator: "Most energy concentrated below ___ kHz?" (student estimates)

**Top-Right Panel (Reconstruction Method & Filter):**
- **Interpolation**: [Zero-order hold] [Linear] [Cubic spline] [Sinc]
- **Reconstruction Filter Type**: [Ideal lowpass] [Butterworth] [Chebyshev] [None]
- **Filter Cutoff**: ━●─ 0.45 F_s (slider from 0.1 F_s to 0.5 F_s)
- **Filter Rolloff**: ━●─ 40 dB/octave (slider from 10 to 100)
- **Preview option**: Checkbox "Show intermediate (pre-filter) reconstruction" in light gray

**Middle Panel (Continuous Reconstruction vs. True Original):**
- Dual plot:
  - Blue: Reconstructed continuous signal x_r(t)
  - Red dashed: True original x(t) (revealed only after student submits or uses hint)
- Overlay of discrete samples as blue dots
- Time axis: several periods of the signal
- Zoom controls to inspect detail
- Metrics:
  - RMS error between x_r and true x
  - PESQ score (for speech)
  - Max absolute error (peak)

**Bottom Panel (Frequency Comparison):**
- **Input spectrum** (from samples, aliased by sampling theorem): shows any aliases
- **Reconstructed spectrum**: before and after lowpass filtering
- **True spectrum**: overlaid in dashed red
- Shaded region: reconstruction filter response
- Readout: "Alias at ___ kHz detected (because F_s too low?)"

### Interaction Model
**Hypothesis → Adjust → Compare loop:**
1. Student sets hypothesized T (sampling period)
2. Chooses interpolation + filter type
3. Adjusts filter cutoff and rolloff
4. Reconstructed signal updates in real-time
5. Compares to true original (or requests hint)
6. On correct guess: "Well done! Sampling rate was 16 kHz. Sinc interpolation with Butterworth filter at 7 kHz reconstructed perfectly."

**Hint system:**
- Hint 1: "Show true original" (reveal red dashed line)
- Hint 2: "Show true spectrum" (reveal frequency content)
- Hint 3: "Show true sampling rate" (reveal F_s)
- Hint 4: "Optimal reconstruction method" (suggest best method)
- Each hint: −10% from max score

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────────┐
│  DISCRETE-TIME RECONSTRUCTION PUZZLE                │
├──────────────┬──────────────────┬──────────────────┤
│ GIVEN x[n]   │ RECONSTRUCTION   │ FREQ COMPARISON │
│ ┌──────────┐ │ ┌──────────────┐ │ ┌──────────────┐│
│ │ • • •   │ │ │ ▔▔▔▔▔▔▔▔▔▔  │ │ │ ▓▓▓▓▓▓▓  ││
│ │  • •  • │ │ │ ▔▔▔▔▔▔▔▔▔▔  │ │ │ ▓▓▓▓▓▓▓  ││
│ │   •    │ │ │ ▔▔▔▔▔▔▔▔▔▔▔▔ │ │ │▓▓▓▓▓▓▓▓▓▓ ││
│ │    •  │ │ │ (---true----)  │ │ │ ▓▓▓▓▓▓▓  ││
│ │ •   •  │ │ │ Error: 3.2%   │ │ │▓▓▓▓▓▓▓▓▓▓ ││
│ │  •   • │ │ │              │ │ │ ▓▓▓▓▓▓▓  ││
│ │   •    │ │ └──────────────┘ │ └──────────────┘│
│ T: ━●─   │ │ Method: [Sinc▼]  │ Alias at 14kHz  │
│ 0.5 ms   │ │ Cutoff: ━●─      │ (F_s too low?)  │
│ (F_s=2kHz)│ │ Rolloff: ━●─     │ True: [?????]   │
└──────────┴──────────────────┴──────────────────┘
RMS Error: 4.2% | PESQ: 3.1/5 | Max Error: 0.18 | [Hint 1] [Hint 2] [Submit] | Score: 750/1000
```

### Key "Aha Moments"
- **"If I pick the wrong sampling rate, I get a completely different signal!"** → Sampling rate is essential information
- **"Sinc interpolation matches the original perfectly, but zero-order hold has visible steps!"** → Reconstruction method matters
- **"There's aliasing in the spectrum at 14 kHz—my sampling rate must be too low!"** → Aliasing is detectable in frequency domain
- **"I reconstructed speech at 8 kHz, but it sounds muffled because I didn't use the Nyquist frequency!"** → Perceptual consequence of aliasing

### Learning Theory Alignment
- **Problem-based Learning**: Solve a mystery (find the original signal)
- **Experiential Discovery**: Students discover Nyquist theorem by trying wrong sampling rates
- **Multi-modal Feedback**: Visual (overlaid signals), frequency (spectrum), perceptual (audio)
- **Transfer**: Insights apply to audio resampling, medical signal reconstruction, radar signal processing

### Technical Architecture
**Backend:**
- Zero-order hold: repeat each sample
- Linear interpolation: scipy.interpolate.interp1d(kind='linear')
- Cubic spline: scipy.interpolate.interp1d(kind='cubic')
- Sinc interpolation: numpy.sinc with window (Hann/Blackman)
- Reconstruction filter: scipy.signal design
- Error metrics: RMSE, PESQ (speech), SSIM (images)

**Frontend:**
- Plotly for continuous signal plots and frequency plots
- Real-time update on slider change
- Overlay of original (dashed) when revealed
- Alias detection: search for spectral peaks outside [0, F_s/2]

### Novelty Claim
**NEVER DONE in S&S education**: Interactive reconstruction puzzle where students infer sampling rate and choose reconstruction method, then see convergence to true original signal. Teaches Nyquist theorem experientially through detective work.

---

## Breakthrough Tool 9: **Time-Frequency Atoms Explorer**
### Category: D (Translation) + E (Physical World)
### Why a Reviewer Would Be Impressed
This tool displays a signal in a spectrogram (time vs. frequency vs. magnitude), but adds a novel interaction: students can click on a time-frequency region and hear that "atom" (a short-duration, narrowband signal component) in isolation. They can also decompose a signal into time-frequency atoms manually (like a reverse spectrogram). The connection to real-world: audio processing, music analysis, speech recognition all use time-frequency decompositions. Reviewers see: "This is how audio engineers think—not in time or frequency alone, but in time-frequency atoms."

### Inspired By (Visual Cues from Slides)
- Lecture 18-2, sheet 03, 06: Effects of phase, DT signals
- Lecture 20, sheet 03: Fourier transforms in physics (Heisenberg uncertainty analogy)
- Lecture 21, sheet 09: Relationship between CT and DT (time-frequency trade-off)

### What Students DO
1. **Load or record a signal** (speech, music, environmental sound)
2. **Compute spectrogram** (STFT: short-time Fourier transform)
3. **Interactive exploration:**
   - Click on a time-frequency region → hear that atom in isolation
   - Hover over spectrogram → see magnitude and frequency readout
   - Adjust window size (trade-off between time and frequency resolution)
4. **Decomposition mode:**
   - Paint on spectrogram to select atoms
   - Reconstruct signal from selected atoms
   - Hear original vs. reconstruction
5. **Challenge**: "Isolate the vowel 'a' from speech; remove background noise"

### Full Description
The **Time-Frequency Atoms Explorer** reveals that signals are not purely time or frequency—they're made of atoms localized in both domains.

**Top-Left Panel (Spectrogram Display):**
- Image plot: time (X-axis, seconds), frequency (Y-axis, Hz), magnitude (color, dB)
- Color scale: dark = quiet, bright = loud
- Interactive: hover to show (t, f, magnitude) tooltip
- Click on a region → extracts and plays that atom
- Zoom and pan controls

**Top-Right Panel (Window & Resolution Controls):**
- **Window Function**: [Hann] [Hamming] [Blackman] [Rectangular]
- **Window Length**: ━●─ 1024 samples
  - Readout: "Time resolution: 23 ms"
  - Readout: "Frequency resolution: 43 Hz"
- **Frequency Scale**: [Linear] [Log (MEL)]
- **Visualization**: [Magnitude (dB)] [Phase] [Group delay]
- Warning indicator: "Shorter window = better time localization, worse frequency resolution"

**Middle Panel (Atom Playback):**
- Large waveform plot: selected atom x_atom(t)
- Duration in samples and milliseconds
- Frequency range in Hz
- **Playback buttons**: [▶ Play atom] [▶ Play original] [▶ Compare (alternating)]
- Volume control (capped at −6 dB)

**Bottom Panel (Decomposition Builder):**
- Copy of spectrogram with mouse-drawable selection
- **Draw mode**: Paint on spectrogram to mark atoms you want
- **Brush size**: Slider [1 pixel to 20 pixels]
- **Color**: Select which atoms (by frequency band or time interval)
- **Reconstruction**: Shows x_reconstruct(t) from selected atoms
- Metrics: "You selected 45% of energy. Reconstruction PESQ: 3.8/5"

### Interaction Model
**Browse → Select → Hear → Reconstruct loop:**
1. Hover on spectrogram → see tooltip
2. Click on bright spot → extracts atom, plays it
3. Drag to select multiple atoms → reconstructs from selection
4. Compare original vs. reconstruction audio
5. Adjust window size → spectrogram updates (time-frequency trade-off visible)

**Atom decomposition:**
- Paint on spectrogram with brush
- Selected regions highlighted in yellow
- Inverse STFT of painted regions → reconstructed signal
- Real-time playback as you paint

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────────┐
│  TIME-FREQUENCY ATOMS EXPLORER                      │
├──────────────────┬──────────────────────────────────┤
│ SPECTROGRAM      │ RESOLUTION CONTROLS              │
│ ┌──────────────┐ │ Window: [Hann ▼]                │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓ │ │ Length: ━●─ 1024 samples      │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓ │ │ Time res: 23 ms                │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓ │ │ Freq res: 43 Hz                │
│ │ ▓▓▓▓░▓▓░▓▓▓▓ │ │ Shorter window →              │
│ │ ▓▓░░░░░░░▓▓ │ │ [better time, worse freq]     │
│ │ ▓░░░░░░░░░░ │ │ Scale: [Linear] [MEL]          │
│ │ ░░░░░░░░░░░ │ │ View: [Magnitude] [Phase] [GD] │
│ │ ░░░░░░░░░░░ │ │ Atom at (0.5s, 800Hz):         │
│ │ ▓░░░░░░░░░░ │ │ Magnitude: −18 dB              │
│ └──────────────┘ │ [▶ Play] [▶ With original]     │
│ t(s) 0   2   4   │                                  │
│ f(Hz)            │                                  │
│ 0                │                                  │
│ 2000             │                                  │
│ 4000             │                                  │
├──────────────────┴──────────────────────────────────┤
│ DECOMPOSITION: Paint atoms on spectrogram           │
│ ┌────────────────────────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓   (yellow = selected)             │ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓                                   │ │
│ │ ▓▓▓▓███████                                   │ │
│ │ ▓▓████████                                    │ │
│ └────────────────────────────────────────────────┘ │
│ Brush: ━●─ | [▶ Original] [▶ Reconstruction]     │
│ Energy selected: 62% | PESQ: 4.1/5                │
└─────────────────────────────────────────────────────┘
Challenge: Isolate the 'a' vowel from speech (1500–3500 Hz, first second) | Progress: 78%
```

### Key "Aha Moments"
- **"This region is bright at low frequency for a short time—that's the vowel onset!"** → Time-frequency structure of speech
- **"When I use a shorter window, I can pinpoint the time better, but the frequency gets fuzzy!"** → Uncertainty principle
- **"If I select only high frequencies and remove the low bass, the speech sounds tinny!"** → Frequency selectivity perception
- **"I can isolate just the violin from this orchestra recording by selecting its time-frequency atoms!"** → Source separation concept

### Learning Theory Alignment
- **Visualization**: Spectrogram makes Fourier transform intuitive (shows how spectrum changes over time)
- **Multi-sensory**: Visual (spectrogram) + Auditory (playback of atoms)
- **Discovery**: Students discover time-frequency trade-off by changing window size
- **Real-world**: Audio processing, speech recognition, music analysis all use spectrograms

### Technical Architecture
**Backend:**
- scipy.signal.stft (short-time Fourier transform)
- Window functions: scipy.signal.get_window
- istft (inverse STFT) for reconstruction
- Magnitude in dB: 20 * log10(|STFT|)
- MEL-frequency scaling (if logarithmic frequency view selected)

**Frontend:**
- Plotly heatmap or Vispy for spectrogram image
- Canvas for interactive spectrogram with drawing mode
- Web Audio API for playback of atoms and reconstructions
- Slider for window length (updates spectrogram in real-time)

### Novelty Claim
**NEVER DONE in S&S education**: Interactive spectrogram where students click to isolate time-frequency atoms and hear them, then paint decompositions and reconstruct from selected atoms. Reveals time-frequency uncertainty principle experientially.

---

## Breakthrough Tool 10: **Feedback Control Stability Simulator**
### Category: B (Design Challenge) + E (Physical World)
### Why a Reviewer Would Be Impressed
Students design a feedback control system (proportional, integral, derivative gains) for a plant (simulated mechanical or electrical system). They see the closed-loop pole locations update in real-time as they adjust gains. They can apply disturbances and see whether the system converges or goes unstable. The multi-domain connection: same feedback principles apply to motors, robots, power supplies, and temperature control. Reviewers see: "Students are designing stable systems—they're not just calculating poles, they're engineering."

### Inspired By (Visual Cues from Slides)
- Lecture 25, sheet 09, 12: Tracking with feedback control, focusing system, laser pointer
- Lecture 17, sheet 03, 06, 09: DT frequency response, complex systems
- Lecture 20, sheet 06: Physical examples (electrocardiogram, CD player mechanics)

### What Students DO
1. **Choose a plant** (process to control): [Leaky tank] [Motor] [Heating system] [Inverted pendulum]
2. **Design a PID controller**: Adjust sliders for K_p, K_i, K_d
3. **Watch the closed-loop system:**
   - Pole-zero map: poles should be inside unit circle (DT) or left half-plane (CT)
   - Step response: should settle without oscillating excessively
   - Root locus as you adjust K_p: shows stability boundary
4. **Apply a disturbance** (step, impulse, ramp input) and see system response
5. **Challenge**: "Control a leaky tank to hold water level at 50 cm; handle a drain disturbance"

### Full Description
The **Feedback Control Stability Simulator** teaches students that stability is paramount—a beautifully designed system that's unstable is useless.

**Top-Left Panel (Plant Selector & PID Gains):**
- **Plant Selection**: [Leaky Tank] [DC Motor] [Temperature Control] [Inverted Pendulum]
- **Plant equation display**: Shows differential or difference equation
- **PID Gains:**
  - K_p (proportional): ━●─ 0.5
  - K_i (integral): ━●─ 0.1
  - K_d (derivative): ━●─ 0.2
- **System info**: "Order: 3 | Type: 1 (integral)"
- **Stability status**:
  - GREEN if all poles on stable side
  - RED if any pole unstable
  - YELLOW if marginally stable

**Top-Right Panel (Pole-Zero Map):**
- Complex plane with unit circle (DT) or imaginary axis (CT)
- Poles (✕) shown and color-coded by gain
- Zero-pole locus shown as B-spline curve
- Root locus: as K_p varies, how poles move
- Stability boundary highlighted
- Readout: "Poles at: [−1.2, −0.5±0.3j] | All stable ✓"

**Middle Panel (Step Response & Frequency Response):**
- Left: Step response u[n]=1 → c[n] output (should approach setpoint without excessive overshoot)
- Right: Bode plot or Nyquist diagram (phase margin, gain margin)
- Shaded region: acceptable response (overshoot <20%, settling time <10 samples)
- Metrics:
  - Rise time
  - Settling time
  - Overshoot
  - Steady-state error

**Bottom Panel (Real-Time Simulation):**
- **Reference signal**: setpoint r[n] shown as dashed line
- **Output c[n]**: solid blue line (plant output)
- **Disturbance injection**: Button "Add step disturbance at t=5" or slider for ramp leak rate
- **Error e[n] = r[n] − c[n]**: dotted red line
- Live update as student adjusts gains
- "Time to settle after disturbance: 0.8 seconds | Steady-state error: 0.2 cm"

### Interaction Model
**Adjust gains → See poles move → Observe response → Verify stability:**
1. Student adjusts K_p slider
2. Pole-zero map updates, poles move along root locus
3. Step response plot updates
4. If poles go unstable (red zone), warning appears
5. Student adjusts K_i and K_d to balance response
6. Applies disturbance to see robustness

**Challenge mode:**
- Scenario: "Maintain water level at 50 cm ± 5 cm. System has a ramp leak that increases over time."
- Student designs PID controller
- Simulation runs 100 seconds with disturbance applied at t=30
- Scoring: How well does system reject disturbance?

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────────┐
│  FEEDBACK CONTROL STABILITY SIMULATOR                │
├───────────────┬──────────────────┬─────────────────┤
│ PID TUNING    │ POLE-ZERO MAP    │ STEP RESPONSE   │
│ Plant: Leaky  │ ┌──────────────┐ │ ┌─────────────┐ │
│ Tank          │ │   jω    ×    │ │ │ ▓▓▓▓▄▄▄▄▄▄│ │
│ K_p: ━●─ 0.5  │ │       ×      │ │ │ ▓▓▓▄▄▄▄▄▄▄│ │
│ K_i: ━●─ 0.1  │ │  ×  ◐  ×    │ │ │ ▓▓▄▄▄▄▄▄▄▄│ │
│ K_d: ━●─ 0.2  │ │       ×      │ │ │ ▓▄▄▄▄▄▄▄▄▄│ │
│ Poles:        │ │   ×    ×    │ │ │ ▄▄▄▄▄▄▄▄▄▄│ │
│ −1.2,         │ │ ⊗──────────→│ │ │            │ │
│ −0.5±0.3j     │ │ ×   ×       │ │ │ [Phase Mgn: │ │
│ Stable ✓      │ │   ×         │ │ │  62°]      │ │
│               │ └──────────────┘ │ └─────────────┘ │
├───────────────┴──────────────────┴─────────────────┤
│ REAL-TIME CLOSED-LOOP RESPONSE                     │
│ ┌───────────────────────────────────────────────┐ │
│ │ 60│                    ▄▄▄▄▄▄▄▄▄             │ │
│ │ 55│ ▓▓▓▄▄▄▄▄▄▄▄▄▄▄▄  │ ▔▔▔▔▔▔▔▔▔ (disturb)│ │
│ │ 50│ ▓▓▄▄▄▄▄▄▄▄▄▄▄▄▄▓▓│            Reference │ │
│ │ 45│ ▓▓▓▓░░░░░░░░░░░▓│ Error     Output     │ │
│ │    └───────────────────────────────────────────┘ │
│ Disturbance: ☑ Leak rate 0.5 cm/min (→Step at t=30)│
│ Time to settle: 2.3s | SS error: 0.1 cm | Safe ✓   │
│ [Apply Disturbance] [Reset] [Challenge Mode]       │
└──────────────────────────────────────────────────────┘
Stability: MARGINAL (Phase margin = 18°, Gain margin = 2.1 dB) | Robustness: FAIR
```

### Key "Aha Moments"
- **"When K_p is too high, the poles cross the stability boundary and the system oscillates forever!"** → Proportional gain limit
- **"Adding integral action (K_i) eliminates steady-state error but can destabilize if too large!"** → PID trade-off
- **"The root locus shows me exactly where the poles move as I increase the gain!"** → Classical control theory visualization
- **"After I tune the controller to handle the normal disturbance, a bigger disturbance breaks it!"** → Robustness vs. nominal performance

### Learning Theory Alignment
- **Authentic Task**: Real feedback control systems (tanks, motors, temperature)
- **Visual Feedback**: Poles moving in real-time on root locus
- **Multi-objective**: Stability, response speed, disturbance rejection, phase margin
- **Transfer**: Same concepts apply to electrical circuits, mechanical systems, power supplies

### Technical Architecture
**Backend:**
- Transfer function or state-space representation of plant
- PID controller implementation: u(t) = K_p * e(t) + K_i * ∫e(t) + K_d * de/dt
- Closed-loop pole computation: pole(s) of T(s) = G(s)*C(s) / (1 + G(s)*C(s))
- Simulation: Runge-Kutta (ODE) or direct DT iteration
- Root locus: vary K_p, compute poles for each K_p value
- Nyquist plot: magnitude and phase of G(jω)C(jω)

**Frontend:**
- Plotly for step response, Bode plot, Nyquist diagram
- Three.js or custom Canvas for pole-zero map with root locus
- Real-time sliders with debounced updates (50ms)
- Web Worker for simulation (prevent UI blocking)

### Novelty Claim
**NEVER DONE in S&S education**: Interactive PID tuning simulator where students adjust gains in real-time, watch poles move on root locus, observe step response, and test disturbance rejection. Combines classical control theory with modern interactive visualization.

---

## Breakthrough Tool 11: **Image Compression Challenge: Wavelets vs. Fourier**
### Category: B (Design Challenge) + E (Physical World)
### Why a Reviewer Would Be Impressed
Students compress an image using two methods: (1) Fourier (keep only largest magnitude coefficients), (2) Wavelets (keep only largest magnitude wavelet coefficients). They adjust the compression ratio (keep N% of coefficients) and compare reconstruction quality (SSIM, visual artifacts). The discovery: wavelets preserve edges better than Fourier, because wavelets are localized in space. Real-world: JPEG uses DCT (Fourier variant); JPEG2000 uses wavelets. Reviewers see: "Students learn why modern image compression switched from Fourier to wavelets—through hands-on comparison."

### Inspired By (Visual Cues from Slides)
- Lecture 22, sheet 03, 07, 11: Quantizing images, Roberts' method, progressive refinement
- Lecture 20, sheet 03: Fourier transforms in physics—crystallography and diffraction
- Lecture 16-2, sheet 03, 05: Fourier transform moments

### What Students DO
1. **Load an image** (face, natural scene, text, artifact)
2. **Compress with Fourier**: Keep top N% of magnitude-sorted coefficients, zero out the rest, inverse FFT
3. **Compress with Wavelets**: Keep top N% of magnitude-sorted wavelet coefficients, zero out the rest, inverse DWT
4. **Adjust compression ratio** [10% to 99% of coefficients kept]
5. **Compare results:**
   - Visual: Fourier shows "ringing" around edges; wavelets preserve edges
   - Metrics: SSIM, MSE, perceptual quality
6. **Challenge**: "Achieve 90% compression (keep 10% of coefficients) with SSIM > 0.8"

### Full Description
The **Image Compression Challenge: Wavelets vs. Fourier** teaches students a profound lesson: different representations are good for different tasks. Fourier excels at smooth signals; wavelets excel at edged signals.

**Top Panel (Image Selector & Compression Ratio):**
- **Image library**: [Face] [Natural scene] [Text document] [Medical image (CT)] [Artifact/artwork]
- **Upload custom image**
- **Compression Slider**: ━●─ 20% (keep 20% of coefficients)
- Readout: "Compression ratio: 5:1 | File size: original 524 KB → compressed 105 KB"

**Middle Panel (Fourier Compression):**
- **Left**: Original image
- **Center**: Magnitude spectrum (log scale), highlighted: which coefficients will be kept
- **Right**: Reconstructed image from top 20% Fourier coefficients
- **Artifact zones**: Red overlay showing "ringing" (Gibbs phenomenon) near edges
- **Metrics panel**:
  - SSIM (Structural Similarity): 0.72
  - MSE: 42.1
  - PSNR: 21.8 dB
  - Artifact severity: HIGH (ringing visible)

**Bottom Panel (Wavelet Compression):**
- **Left**: Original image
- **Center**: Wavelet coefficient tree (hierarchical, coarse to fine)
  - Top-left: low-pass (smooth) components, size ↑
  - Top-right, bottom-left, bottom-right: detail components at multiple scales
  - Highlighted: which coefficients will be kept
- **Right**: Reconstructed image from top 20% wavelet coefficients
- **Artifact zones**: Minimal (edges preserved, no ringing)
- **Metrics panel**:
  - SSIM: 0.91
  - MSE: 8.3
  - PSNR: 28.8 dB
  - Artifact severity: LOW (sharp edges preserved)

**Comparison View (Optional Toggle):**
- Side-by-side Fourier vs. Wavelet reconstruction
- Difference image (error heat map)

### Interaction Model
**Adjust compression ratio → See both methods update:**
1. Drag compression slider
2. Fourier reconstruction updates (real-time)
3. Wavelet reconstruction updates (real-time)
4. Metrics update: SSIM, MSE, artifact severity
5. Visual feedback: where does each method fail?

**Challenge mode:**
- Scenario: "Compress this face image to 90% (keep 10% of coefficients) with SSIM > 0.8"
- Student adjusts slider and chooses method
- Submits answer
- Scoring: Based on SSIM achieved and method used

### Multi-Panel Layout
```
┌────────────────────────────────────────────────────┐
│  IMAGE COMPRESSION CHALLENGE: Wavelets vs. Fourier │
├────────────────────────────────────────────────────┤
│ Image: Face | Compression: ━●─ 20% (80% discarded)│
├────────────────┬───────────────┬──────────────────┤
│ FOURIER METHOD │ SPECTRUM/TREE │ WAVELET METHOD   │
│ ┌────────────┐ │ ┌──────────┐  │ ┌────────────┐  │
│ │ Original   │ │ │ Kept:███░│  │ │ Original   │  │
│ │ ▓▓▓▓▓▓▓   │ │ │ Discard:░│  │ │ ▓▓▓▓▓▓▓   │  │
│ │ ▓▓▓▓▓▓▓   │ │ │ ▓▓▓▓▓▓▓▓▓│  │ │ ▓▓▓▓▓▓▓   │  │
│ │ ▓▓▓▓▓▓▓   │ │ │ 20% size │  │ │ ▓▓▓▓▓▓▓   │  │
│ │ ▓▓▓▓▓▓▓   │ │ │          │  │ │ ▓▓▓▓▓▓▓   │  │
│ │ ▓▓▓▓▓▓▓   │ │ │          │  │ │ ▓▓▓▓▓▓▓   │  │
│ └────────────┘ │ │(Tree vis)│  │ └────────────┘  │
│ Ringing near   │ └──────────┘  │ Edges preserved │
│ edges (RED)    │               │ No ringing      │
│ ┌────────────┐ │               │ ┌────────────┐  │
│ │ Fourier    │ │               │ │ Wavelet    │  │
│ │ Recon      │ │               │ │ Recon      │  │
│ │ ▓▓▓▓▓▓ ~~~│ │               │ │ ▓▓▓▓▓▓▓   │  │
│ │ ▓▓▓▓▓▓ ~~~│ │               │ │ ▓▓▓▓▓▓▓   │  │
│ │ ▓▓▓▓▓▓▓   │ │               │ │ ▓▓▓▓▓▓▓   │  │
│ └────────────┘ │               │ └────────────┘  │
│ SSIM: 0.72    │               │ SSIM: 0.91     │
│ MSE: 42.1     │               │ MSE: 8.3       │
│ PSNR: 21.8 dB │               │ PSNR: 28.8 dB  │
└────────────────┴───────────────┴──────────────────┘
Challenge: Achieve SSIM > 0.8 at 90% compression (10% kept) | Your best: Wavelets, SSIM 0.82
```

### Key "Aha Moments"
- **"The Fourier method has ringing around sharp edges, but wavelets don't!"** → Wavelets are spatially localized
- **"Most image energy is in low frequencies, but the important information is in the edges!"** → Fourier emphasis on energy ≠ visual quality
- **"I can get 90% compression with wavelets and still recognize the face!"** → Wavelets are effective for natural images
- **"Fourier compression looks like old JPEG artifacts—that's Gibbs phenomenon!"** → Historical understanding of why JPEG switched to DCT/wavelets

### Learning Theory Alignment
- **Comparison Learning**: Side-by-side of two methods reveals strengths/weaknesses
- **Real-world Context**: JPEG vs. JPEG2000 historical note
- **Multi-objective**: Balance compression ratio with visual quality
- **Transfer**: Same concepts apply to video (H.264 uses wavelets), medical imaging

### Technical Architecture
**Backend:**
- 2D FFT (scipy.fft.fft2) for Fourier compression
- Discrete Wavelet Transform (pywt.wavedec2 with 'db4' or 'bior3.5')
- Threshold coefficients by magnitude, keep top N%
- Inverse FFT and inverse DWT
- SSIM, MSE, PSNR computation

**Frontend:**
- Plotly for original + reconstructed images
- Heatmap for difference/error
- Real-time slider update (debounced 150ms)
- Wavelet tree visualization (nested boxes showing scales)

### Novelty Claim
**NEVER DONE in S&S education**: Side-by-side interactive compression using Fourier vs. wavelets, with real-time SSIM/artifact metrics, revealing why modern compression switched from Fourier to wavelets.

---

## Breakthrough Tool 12: **Pole Placement & Stability Cross-Domain Visualizer**
### Category: F (Composition) + E (Physical World)
### Why a Reviewer Would Be Impressed
This tool unifies pole-zero analysis across four engineering domains: electrical circuits, mechanical vibrations, control systems, and signal filtering. Students place poles on a complex plane, then see how that choice affects behavior in all four domains simultaneously. For example, placing a pole at −1+2j shows: circuit response (damping, resonance), mechanical response (acceleration, position), filter response (magnitude/phase), and control response (step response). The breakthrough: students see that pole placement is a universal concept, not four separate theories. Reviewers see: "This is how modern engineers think—domain-agnostic, unified theory."

### Inspired By (Visual Cues from Slides)
- Lecture 17, sheet 03, 06, 09: Pole-zero relationship to frequency response
- Lecture 18-2, sheet 03, 06: Effects of poles on phase and magnitude
- Lecture 25, sheet 03: Applications across domains (ECG, CD, radar)

### What Students DO
1. **Start with an empty pole-zero plane** (complex plane with unit circle or imaginary axis)
2. **Drag to place poles** (each pole placement marked by ✕ and labeled)
3. **Simultaneously see four domain-specific views update:**
   - **Electrical**: Impedance Z(jω) = 1/(s + pole), frequency response
   - **Mechanical**: m¨x + c˙x + kx = F input, step response acceleration
   - **Control**: Step response of system with given pole
   - **Signal**: Magnitude and phase response |H(jω)|, ∠H(jω)
4. **Challenge**: "Place poles to create a low-pass filter with cutoff −3 dB at 100 Hz and zero overshoot"

### Full Description
The **Pole Placement & Stability Cross-Domain Visualizer** reveals that pole-zero analysis is the Rosetta Stone of engineering—the same mathematics describes different physical systems.

**Top-Left Panel (Pole-Zero Plane Editor):**
- Complex plane: Real (σ) on X-axis [−10 to +1], Imaginary (ω) on Y-axis [−10j to +10j]
- Unit circle (DT) or imaginary axis (CT) shown
- Stability region shaded (left half-plane for CT, inside unit circle for DT)
- Interactive: click to add poles, drag to move, right-click to delete
- Currently placed poles listed below:
  - Pole 1: −0.5 + 1.2j
  - Pole 2: −2.0 (real)
  - "Natural frequency: 1.3 rad/s | Damping: 0.35 (underdamped)"

**Top-Right Panel (4-Domain Dashboard):**
- Four sub-views, each showing a different domain perspective:

1. **Electrical Circuit (top-left):**
   - Magnitude of transfer function |H(jω)| vs. frequency
   - Frequency response plot (linear or log scale)
   - Key metrics: resonance frequency, Q factor, bandwidth

2. **Mechanical System (top-right):**
   - Step response of position x(t)
   - Shows characteristic behavior: underdamped (oscillatory), critically damped, overdamped
   - Overshoot %, settling time, frequency of oscillation

3. **Control System (bottom-left):**
   - Step response of closed-loop system
   - Rise time, settling time, overshoot
   - Stability margin: "Stable ✓" or "Unstable ✗"

4. **Filter Response (bottom-right):**
   - Bode magnitude plot (dB vs. log frequency)
   - Bode phase plot (degrees)
   - Nyquist plot (option to toggle)

### Interaction Model
**Drag poles → All four views update instantly:**
1. Click on pole-zero plane to add a new pole (or pair of complex-conjugate poles)
2. Drag pole to new location
3. All four domain views update in real-time:
   - Electrical: resonance shifts to new frequency
   - Mechanical: oscillation frequency changes, damping changes
   - Control: step response overshoot changes
   - Filter: passband/stopband shape changes
4. Metrics update automatically

**Preset modes:**
- **Real pole**: one pole on negative real axis (no oscillation)
- **Complex pair**: two poles, symmetric about real axis (oscillatory)
- **Marginal pole**: pole on imaginary axis (marginal stability, pure oscillation)

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────────┐
│  POLE PLACEMENT & STABILITY CROSS-DOMAIN VISUALIZER  │
├─────────────────┬───────────────────────────────────┤
│ POLE-ZERO PLANE │ ELECTRICAL DOMAIN                │
│ ┌──────────────┐│ ┌────────────────────────────────┐│
│ │      jω      ││ Magnitude Response              ││
│ │      │    ×  ││ ┌──────────────────────────────┐││
│ │  ────┼───────││ │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓           │││
│ │      │       ││ │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (peak)   │││
│ │    ⊗─┼───×───││ │  ▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓ ▓           │││
│ │  σ   │       ││ │  ▓▓▓▓▓ ▓ ▓▓▓▓▓▓▓▓▓           │││
│ │      │   ×   ││ └──────────────────────────────┘││
│ │      │       ││ f_res = 1.3 Hz, Q = 2.1        ││
│ │      ●       ││                                 ││
│ └──────────────┘│                                  │
│ Poles: 2        │ MECHANICAL DOMAIN               │
│ −0.5±1.2j       │ ┌────────────────────────────────┐│
│ f_n = 1.3 rad/s │ Step Response                  ││
│ ζ = 0.35        │ ┌──────────────────────────────┐││
│ (underdamped)   │ │  ▄▄▄▄▄▄▄▄▄                   │││
│                 │ │ ▄▄▄▄▄▄▄▄▄▄▄▄ (overshoot)    │││
│ [Add Pole]      │ │▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄             │││
│ [Delete]        │ │▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ (steady)    │││
│ [Preset: Real]  │ └──────────────────────────────┘││
│ [Preset: Complex]│ OS: 35.2% | t_settle: 1.8s    ││
└─────────────────┴───────────────────────────────────┘
│ CONTROL DOMAIN              │ FILTER RESPONSE            │
│ ┌──────────────────────────┐│ ┌──────────────────────────┐│
│ │ Step Response            ││ │ Magnitude (dB)          ││
│ │ ▓▓▓▄▄▄▄▄▄▄▄▄            ││ │ ▓▓▓▓▓▓▓▓▓ -3dB @ 1.3Hz ││
│ │ ▓▓▓▄▄▄▄▄▄▄▄▄            ││ │ ▓▓▓▓▓▓▓ ▓ ▓ ▓          ││
│ │ ▓▓▄▄▄▄▄▄▄▄▄▄            ││ │ ▓▓▓▓▓ ▓ ▓ ▓ ▓          ││
│ │ ▓▄▄▄▄▄▄▄▄▄▄▄            ││ │ ▓▓▓▓ ▓ ▓ ▓ ▓           ││
│ │ ▄▄▄▄▄▄▄▄▄▄▄▄            ││ │ ▓▓▓▓ ▓ ▓ ▓ ▓ (rolloff) ││
│ │ Stable ✓ Rise: 0.5s    ││ │ Rolloff: -40 dB/dec    ││
│ └──────────────────────────┘│ └──────────────────────────┘│
└──────────────────────────────────────────────────────────┘
Challenge: Design lowpass filter: 3dB @ 100 Hz, no overshoot | Hints: [Real pole placement], [Complex pair]
```

### Key "Aha Moments"
- **"Moving this pole closer to the origin makes the oscillation slower!"** → Pole distance ↔ frequency
- **"When both poles are real, there's no overshoot—the response is smooth!"** → Real poles = monotonic decay
- **"The same pole location means the same damping for a spring, the same circuit resonance, the same filter shape!"** → Universal principle
- **"If a pole crosses into the right half-plane, everything becomes unstable!"** → Stability is pole location-dependent

### Learning Theory Alignment
- **Unified Theory**: Students see that pole-zero analysis is domain-agnostic
- **Multi-sensory**: Visual poles + numerical metrics + graphical responses
- **Transfer Across Domains**: Insights from one domain (e.g., mechanical) apply to all
- **Active Learning**: Dragging poles engages kinesthetic learning

### Technical Architecture
**Backend:**
- Transfer function H(s) constructed from pole locations
- scipy.signal.freqs for continuous-time frequency response
- scipy.signal.step for step response
- Bode plot: magnitude and phase
- Nyquist plot: real vs. imaginary parts
- Metrics: natural frequency, damping ratio, Q factor, overshoot, settling time

**Frontend:**
- Three.js or D3.js for pole-zero plane editor (draggable markers)
- Plotly for 4 sub-views (magnitude, step response, etc.)
- Real-time update on drag (no debounce needed, visual feedback is immediate)
- Color coding: poles stable (blue), unstable (red), marginally stable (yellow)

### Novelty Claim
**NEVER DONE in S&S education**: Interactive pole placement showing simultaneous feedback across four engineering domains (electrical, mechanical, control, filtering). Reveals pole-zero analysis as a universal design tool, not domain-specific.

---

# Summary Table: 12 Breakthrough Tools

| Tool | Category | Why Novel | Key Insight |
|------|----------|-----------|------------|
| 1. Harmonic Decomposition Sculptor | F + E | Auditory + visual + kinesthetic harmonic synthesis | Hearing harmonics builds intuition better than seeing them |
| 2. Fourier Transform Crystallographer | E + D | 2D Fourier with interactive masking and reconstruction | X-ray crystallography + MRI connect Fourier theory to real imaging |
| 3. Sampling Alias Detector Game | G + A | Gamified alias reverse-engineering with timed challenges | Aliasing becomes a competitive detective game, not a hazard |
| 4. Modulation Radar Constructor | F + E | FM/AM design with Doppler feedback and interference zones | Modulation theory applied to radar—real engineering problem |
| 5. Phase-Frequency Domain Navigator | D + F | 3D simultaneous magnitude + phase with real-time adjustment | Phase revealed as fundamental, not secondary; Heisenberg uncertainty made tangible |
| 6. Quantization Forensics Lab | A + E | Reverse-engineer bit depth, method, and artifacts; use dithering to improve | Quantization becomes forensics; dithering trades noise for quality |
| 7. Filter Design Showdown | F + G | Real-time pole-zero + frequency response + leaderboard | Modern engineers don't hand-calculate; they interact with real-time feedback |
| 8. Discrete-Time Reconstruction Puzzle | A + B | Infer sampling rate, choose reconstruction method, compare to original | Nyquist theorem discovered through experimentation, not calculation |
| 9. Time-Frequency Atoms Explorer | D + E | Interactive spectrogram with click-to-hear atoms and paint-to-decompose | Spectrogram demystifies how audio engineers think (time-frequency, not time-only) |
| 10. Feedback Control Stability Simulator | B + E | PID tuning with root locus, step response, disturbance rejection | Feedback control unified across motors, tanks, heating—domain-agnostic |
| 11. Image Compression Challenge | B + E | Fourier vs. wavelets, side-by-side with SSIM/artifact metrics | Why JPEG2000 beat JPEG: wavelets preserve edges; Fourier produces ringing |
| 12. Pole Placement Cross-Domain Visualizer | F + E | Drag poles, see effects in electrical, mechanical, control, and filter domains simultaneously | Pole-zero analysis is universal; same math describes different physics |

---

# Conference Talking Points

**For reviewers who ask, "Why is this different from existing tools?"**

1. **Multi-modal feedback**: Most tools show one representation (time, or frequency, or phase). Our tools show 2–4 simultaneously and let students interact with all at once.

2. **Gamification with rigor**: Challenge modes and leaderboards don't trivialize concepts; they incentivize deep understanding through competition and speed.

3. **Cross-domain linking**: Instead of 13 isolated simulations, these tools reveal that the same principle (e.g., pole placement, Fourier decomposition) solves problems in electrical, mechanical, optical, and control domains.

4. **Authentic engineering workflows**: Students don't calculate transfer functions by hand; they interact with them. This mirrors how real engineers design filters, control systems, and compressed data.

5. **Constructivism at scale**: Students don't just observe—they build, decompose, reverse-engineer, and design. Every tool is a "doing" tool, not a "watching" tool.

---

