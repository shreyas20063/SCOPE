# Interactive Tools for MIT 6.003 Lectures 19-25
## Fourier Relations, Sampling, Modulation & Applications

---

## Tool 1: Fourier Domain Navigator
### Inspired By (Visual)
Lecture 19 contact sheets show the **four Fourier representations** as a 2x2 grid with arrows showing transformations:
- Periodic/Aperiodic time vs. Periodic/Aperiodic frequency
- "Relations among Fourier Representations" diagram (sheet 09, 24)
- Sampling in time → spectral replication; periodic extension → frequency sampling

### What Students DO (not watch)
- **Drag signals** between the four representations (CTFS ↔ CTFT ↔ DTFS ↔ DTFT)
- **Click arrows** to trigger transformations (sampling, periodic extension, interpolation)
- **Watch domains morph** in real-time as they adjust signal properties
- **Build intuition** about which representation best reveals signal structure
- **Construct** their own signals in one domain and see what emerges in others

### Tool Description
A four-panel interactive workspace where students explore the duality between time and frequency domains, and between continuous and discrete representations. The central mechanic: **dragging a manipulable signal in any domain automatically updates the other three**. Students see how sampling a CT signal creates spectral replication, how periodic extension creates frequency sampling, and how these transformations relate.

Panel layout:
- **Top-left:** CT Fourier Series (periodic time, discrete frequency)
- **Top-right:** CT Fourier Transform (aperiodic time, continuous frequency)
- **Bottom-left:** DT Fourier Series (periodic discrete time, periodic frequency)
- **Bottom-right:** DT Fourier Transform (aperiodic discrete time, periodic frequency)

Each panel has:
- Animated signal/spectrum plot
- Draggable control points to shape signal
- Sliders for period T, sampling rate fs
- Parameter read-outs showing key relationships (e.g., Ω = ωT, frequency spacing = 2π/N)

Interaction: Drag a control point in any plot → all four update. Change T or fs → watch spectral spacing adjust. Draw a signal in time domain → see its frequency content appear automatically.

### Multi-Panel Layout
```
┌─────────────────────────────────────────────────────┐
│  Fourier Domain Navigator                           │
├──────────────────────┬──────────────────────────────┤
│   CT Fourier Series  │  CT Fourier Transform        │
│  (time periodic)     │  (time aperiodic)            │
│ [plot + draggable]   │ [plot + draggable]           │
│ ↓ periodic ext (→T) ↓│ ↓ sample (÷T) ↓             │
├──────────────────────┼──────────────────────────────┤
│   DT Fourier Series  │  DT Fourier Transform        │
│ (time periodic)      │  (time aperiodic)            │
│ [plot + draggable]   │ [plot + draggable]           │
│  ↓ N→∞ ↓             │  ↓ interpolate ↓             │
└──────────────────────┴──────────────────────────────┘
Sliders: Period T | Sampling Rate fs | Window N
Read-outs: ω₀ = 2π/T, Ω = ωT, Δω = 2π/N, Δf = fs/N
```

### Key "Aha Moments"
1. **Sampling in time = replication in frequency.** Drag sampling rate slider down → watch spectral copies get closer (approaching aliasing).
2. **Periodic extension = frequency sampling.** Make a signal periodic → frequency spectrum snaps to discrete impulses, spaced by 1/T.
3. **Four representations are the same signal.** Modify one → all four change together. Pick whichever representation makes the problem easiest.
4. **Relations between parameters.** Ω = ωT is not abstract; watch it happen live as you adjust fs.
5. **Limit behavior.** As N→∞, DTFS becomes DTFT. As T→∞, CTFS becomes CTFT.

### Technical Architecture
**Backend:**
- Simulator computes all four representations from user-drawn signal
- Python: Accept time-domain samples x[n] or parametric signal (e.g., sum of sinusoids)
- Compute DTFS, DTFT, then interpolate/sample to get CTFS, CTFT
- Return four sets of {id, title, data[], layout} for Plotly
- Handle aliasing visualization (spectral copies)
- DataHandler serializes NumPy FFTs and frequency grids

**Frontend:**
- Split-pane layout with 2x2 Plotly plots
- Draggable control points on time-domain plots (x[n] or x(t))
- Sliders: T (period), fs (sampling rate), N (DT period length)
- Real-time computation + debounce (150ms)
- Synchronized zoom/pan across all four panes (uirevision sync)
- Read-out panel showing: ω₀, Ω, Δω, Δf, fs, fNyquist, relationship equations

**Complexity:** Medium. Requires FFT computation for all four transforms; careful alignment of frequency axes; handling of edge cases (very small/large T, fs near Nyquist).

### Why This Isn't Generic
This is not "adjust slider, see plot change." It's a **constraint-based explorer**. Each of the four domains is a valid "view" of the same signal; changes ripple across all four. This directly addresses Lecture 19's central claim: the four Fourier representations are not separate tools—they're different lenses on one underlying structure. Students don't memorize the four formulas; they **see why they're equivalent**.

---

## Tool 2: Aliasing Discovery Lab
### Inspired By (Visual)
Lecture 21 contact sheets extensively show **aliasing diagrams**:
- Spectral copies wrapping around ±ωs/2 (sheets 27-34)
- Frequency mapping: input frequency → output frequency via modular arithmetic
- Anti-aliasing filter (sheet 54)
- Music aliasing demonstration (sheet 49)
- Lecture 22 shows quantization artifacts (sheets 8-30)

### What Students DO (not watch)
- **Compose a multi-frequency signal** (add sinusoids at user-chosen frequencies)
- **Choose sampling rate** (slider to adjust fs)
- **Watch frequencies "wrap"** in real-time; above Nyquist fold back down
- **Predict aliases** before seeing them (predict → check mechanic)
- **Experiment with anti-aliasing filters** (drag cutoff frequency, see how it prevents wrapping)
- **Design a filter** to remove high frequencies before sampling
- **Challenge mode:** Given a downsampled signal, reverse-engineer the original by identifying which frequencies aliased

### Tool Description
A highly interactive sandbox for exploring aliasing. Students build a signal from sinusoid components (draggable frequency sliders), set a sampling rate, and **watch frequency components map** to their aliases in real-time. A key mechanic: **sliding the sampling rate** causes frequencies to "slide along the frequency axis" as aliases appear and disappear.

The tool visualizes:
1. **Input spectrum** (before sampling): all components shown as vertical lines
2. **Sampling impulse train in frequency** (periodically spaced copies centered at integer multiples of fs)
3. **Output spectrum** (after sampling): the "folded" version where any frequency component outside [-fs/2, fs/2] wraps back into the passband
4. **Frequency mapping plot:** A "wrap-around" diagram showing input frequency (x-axis) → output frequency (y-axis)

Students can:
- Draw sinusoid frequencies by clicking on a frequency axis (adds a component)
- Drag frequency markers to change them
- Drag the Nyquist frequency slider (adjusts fs)
- Toggle anti-aliasing filter on/off (shows LPF before sampling)
- Play audio samples to hear aliasing distortion

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────────┐
│  Aliasing Discovery Lab                              │
├──────────────────────────────────────────────────────┤
│  Input Signal Spectrum (add sinusoids by clicking)   │
│  [Frequency axis: 0 to 200 kHz, markers draggable]  │
│  │ o │    o     │        o          │               │
│  │ 5│    47 │        100│           │               │
├──────────────────────────────────────────────────────┤
│  After Sampling at fs = [slider 0-220 kHz]          │
│  │ o │    o     │        o          │               │
│  │ 5│    47 │        100→44 (alias) │               │
│                                                      │
│  Predicted aliases:    ☐ 5 kHz       ☑ 44 kHz      │
│  Click [Show] to verify → updates output spectrum  │
├──────────────────────────────────────────────────────┤
│  Frequency Mapping (input → output after sampling)   │
│  y=x (no wrap)  vs.  y = |x mod fs, fold at fs/2|  │
│  [2D plot showing wrapping geometry]                │
├──────────────────────────────────────────────────────┤
│  ☐ Enable Anti-Aliasing Filter (cutoff = [slider])  │
│  [Shows LPF magnitude response overlaid on input]    │
├──────────────────────────────────────────────────────┤
│  Audio: [Play original] [Play sampled] [Play alias] │
└──────────────────────────────────────────────────────┘
```

### Key "Aha Moments"
1. **Nyquist isn't magic; it's geometry.** Dragging fs slider shows frequencies literally wrapping around at Nyquist. Makes the "folding" physically intuitive.
2. **Anti-aliasing is essential.** Toggle the LPF on/off → watch high-frequency components disappear before they can alias. Audio quality transforms.
3. **Aliasing is frequency modular arithmetic.** If fs = 44.1 kHz and you try to sample a 66 kHz tone, it wraps to 44.1 - 22 = 22 kHz (or more generally, (66 mod 88.2) - 44.1). Makes the math concrete.
4. **You can construct indistinguishable signals.** Two completely different input signals can have identical samples if their frequency content differs by a multiple of fs.
5. **Prediction → verification loop.** "If I sample at 44 kHz, will a 100 kHz tone alias to 22 kHz?" Check by clicking a button. Builds predictive intuition.

### Technical Architecture
**Backend:**
- Receive: list of sinusoid frequencies {f1, f2, ...}, amplitude, sampling rate fs
- Compute: which frequencies alias to which output frequencies using folding formula
  - If f < fs/2: output = f
  - If fs/2 < f < fs: output = fs - f
  - If f > fs: recursively apply wrapping rule
- Generate three spectrum plots: input, output, folding map
- Optionally apply LPF transfer function H(jω) before computing aliases
- Return plots + numerical predictions

**Frontend:**
- Interactive frequency axis: click to add sinusoid, drag to adjust frequency
- Large fs slider (horizontal) with visual Nyquist marker
- Real-time updates (debounce 150ms)
- Prediction input box: user types frequency → system computes alias, student confirms
- Audio playback of original and aliased signals (Web Audio API)
- Color coding: frequencies in passband (green), frequencies that will alias (red/orange)

**Complexity:** Medium-High. Requires accurate frequency wrapping logic, audio synthesis for playback, and responsive UI for dragging/predicting.

### Why This Isn't Generic
This tool makes aliasing **visceral and predictable**, not an abstract formula. Students see the geometry of wrapping, hear the aliasing distortion, and build mental models through prediction + verification. It's not a simulation of sampling; it's an **interactive algebra** of aliasing.

---

## Tool 3: Sampling & Reconstruction Pipeline
### Inspired By (Visual)
Lecture 21 shows the **complete sampling/reconstruction chain** (sheets 13-26):
- Continuous signal x(t)
- Impulse train multiplication p(t) with period T
- Impulse reconstruction xp(t) = Σ x[n]δ(t - nT)
- Bandlimited LPF reconstruction xr(t)
- Effect of undersampling + anti-aliasing filter (sheets 54-59)

Lecture 22 extends this with **quantization** (sheets 8-30):
- Input amplitude mapping to discrete levels
- Bit-depth effects (2, 3, 4, 8, 16 bits)
- Dithering vs. no dither (sheets 23-35)
- Robert's technique (sheets 36-42)

### What Students DO (not watch)
- **Draw a CT signal** (sketch or use preset signals: sine, triangle, chirp, speech)
- **Adjust sampling rate** (slider or Hz input) and **watch impulse samples appear**
- **Drag the ideal LPF cutoff** and **see reconstructed signal update**
- **Adjust quantization levels** (2-16 bits) and **see amplitude quantization appear**
- **Toggle dithering** and **observe noise-shaping effects**
- **Compare input vs. output** (error plot showing reconstruction error)
- **Challenge:** Match the output to the input by tuning fs and filter cutoff

### Tool Description
A **complete analog-to-digital-to-analog chain** where students see all transformations step-by-step:
1. **Input:** Draw or upload a continuous signal
2. **Sampling stage:** Choose fs, watch impulse samples appear
3. **Quantization stage:** Choose bit depth, watch amplitude discretization
4. **Reconstruction stage:** Choose LPF cutoff, watch sinc-based reconstruction
5. **Output:** Compare reconstructed signal to original; measure error

The tool displays signal at all stages (input, impulse samples, quantized samples, reconstructed output) in synchronized panels. Sliders control fs, LPF cutoff, bit depth, and optionally dithering amount.

### Multi-Panel Layout
```
┌────────────────────────────────────────────────────────┐
│  Sampling & Reconstruction Pipeline                   │
├────────────────────────────────────────────────────────┤
│ Input x(t)              │ Impulse Samples x[n]δ(t-nT) │
│ [draw or preset]        │ [impulse train at nT]       │
│ [smooth curve]          │ [discrete samples visible]  │
├─────────────────────────┼─────────────────────────────┤
│ Quantized Samples       │ Reconstructed xr(t)         │
│ (bit-depth: [slider])   │ (LPF cutoff: [slider])      │
│ [staircase/quantized]   │ [sinc interpolation]        │
├────────────────────────────────────────────────────────┤
│ Error: xr(t) - x(t)     │ Reconstruction Quality      │
│ [error signal]          │ SNR: [dB], MSE: [value]     │
├────────────────────────────────────────────────────────┤
│ Controls:                                              │
│ Sampling rate fs: [dropdown: 8kHz, 16kHz, 44.1kHz...] │
│ LPF cutoff ωc: [slider 0 to ωs/2]                     │
│ Bit depth: [2] [3] [4] [8] [16]                       │
│ ☐ Dithering (amount: [slider])                        │
│ ☐ Robert's technique                                   │
│ [Play original] [Play quantized] [Play reconstructed]│
└────────────────────────────────────────────────────────┘
```

### Key "Aha Moments"
1. **Sampling is multiplication by impulse train.** See the impulses appear at times nT. Helps students visualize why Fourier multiplication becomes convolution in frequency.
2. **Reconstruction isn't magic; it's sinc interpolation.** Watch the sinc functions emerge and sum to recreate the signal. Builds intuition for the sampling theorem.
3. **Lowpass filter is essential for reconstruction.** Cutoff below Nyquist → perfect (or near-perfect) reconstruction. Cutoff above Nyquist → aliasing in output.
4. **Quantization error ≠ aliasing.** Bit depth limits affect amplitude precision, not frequency content. Dithering trades visible banding for inaudible noise.
5. **CD design trade-offs:** 44.1 kHz sampling, 16 bits quantization, dithering, oversampling filters—each choice becomes clear through hands-on experimentation.

### Technical Architecture
**Backend:**
- Input: signal x(t) [parametric or sampled], fs, LPF cutoff ωc, bit depth B, dither flag
- Stage 1 (Sampling): Evaluate x at times nT; create impulse train in frequency domain
- Stage 2 (Quantization): Quantize amplitudes to B bits; optionally add dither noise then quantize
- Stage 3 (Reconstruction): Apply ideal LPF with cutoff ωc; compute sinc interpolation or equivalent
- Compute error: MSE, SNR, spectrum of error signal
- Return plots: input, samples, quantized, reconstructed, error, quality metrics

**Frontend:**
- Signal drawing canvas (or preset library: sine, triangle, chirp, recorded audio)
- Synchronized time-domain plots for all stages
- Sliders for fs, ωc, bit depth
- Toggle buttons for dithering and Robert's technique
- Real-time playback (Web Audio API) of quantized and reconstructed audio
- Error visualization: overlay of original vs. reconstructed, error waveform, frequency spectrum of error

**Complexity:** High. Requires sinc interpolation (or FFT-based windowing), accurate quantization with optional dithering, multiple plots synchronized, audio playback with low latency.

### Why This Isn't Generic
This tool makes **every step of the AD/DA chain visible**. It's not a black box; students see the impulses, the sinc functions, the quantization levels, and the reconstruction error. This is a **complete system explorer**, not a parameter-adjustment tool. It teaches the entire pipeline from Lecture 21-22.

---

## Tool 4: Modulation & Demodulation Studio
### Inspired By (Visual)
Lectures 23-24 show extensive **modulation diagrams**:
- AM: multiplication in time = convolution in frequency (sheets showing frequency shift)
- Synchronous demodulation (sheet 16-18): multiply again by carrier, then LPF
- Frequency-division multiplexing (sheets 19-23): multiple carriers, selective demodulation
- FM: phase/frequency modulation with increasing modulation index m (sheets 9-30 showing bandwidth expansion with Bessel functions)
- Phase lock and carrier recovery challenges

### What Students DO (not watch)
- **Build a transmitter:** Choose message signal (draw or preset), choose modulation type (AM/PM/FM), set carrier frequency
- **Drag modulation parameters** (modulation index m, carrier frequency ωc) and watch **time-domain waveform and spectrum update**
- **Build a receiver:** Choose demodulation method (synchronous, envelope detection)
- **Adjust receiver carrier frequency** and watch **demodulation quality degrade** if phase/frequency mismatch
- **Multi-channel scenario:** Multiple transmitters on different carriers; select one to demodulate by tuning receiver
- **Interactive phase lock:** See how phase shift between transmitter and receiver causes signal fading
- **Compare modulation schemes:** AM vs. FM side-by-side, see bandwidth trade-offs and noise robustness

### Tool Description
A **modulation/demodulation laboratory** where students build transmitter-receiver pairs and explore how different modulation schemes encode information in different domains (amplitude vs. frequency vs. phase).

**Transmitter side:**
- Message signal: draw, upload, or choose preset (voice, sinusoid, chirp)
- Modulation type selector: AM, AM with carrier, PM, FM
- Carrier frequency ωc (slider or Hz input)
- Modulation index m (for FM/PM)
- Real-time plots: message signal, modulated signal (time), spectrum of modulated signal

**Receiver side:**
- Demodulation type selector: synchronous (multiply by carrier + LPF), envelope detector (for AM+C)
- Receiver carrier frequency (with phase and frequency error sliders)
- Received signal (can be the transmitted signal, or with noise/multipath)
- Real-time plots: received signal, demodulated signal, spectrum analysis, error metric

**Multi-channel mode:**
- Three simultaneous transmitters at different frequencies (ωc1, ωc2, ωc3)
- Receiver tunes to one by choosing demodulation frequency
- Sliders show how selectivity improves with narrower filters

### Multi-Panel Layout
```
┌────────────────────────────────────────────────────────────┐
│  Modulation & Demodulation Studio                         │
├────────────────────────────────────────────────────────────┤
│ MESSAGE SIGNAL              │ TRANSMITTED SIGNAL           │
│ [draw or preset]            │ m(t) × cos(ωct)              │
│ [time plot]                 │ [modulated waveform]         │
│                             │ [carrier frequency chosen]   │
├────────────────────────────────────────────────────────────┤
│ MESSAGE SPECTRUM            │ TRANSMITTED SPECTRUM         │
│ [baseband 0-5kHz]           │ [centered at ωc]             │
│                             │ [AM: ±5kHz around ωc]        │
│                             │ [FM: wider, depends on m]    │
├────────────────────────────────────────────────────────────┤
│ DEMODULATION                │ RECOVERED MESSAGE            │
│ Type: [AM] [AM+C] [PM] [FM]│ [recovered signal]           │
│ Receiver carrier            │ [compare to original]        │
│  Freq: [slider ωc±Δω]       │                              │
│  Phase: [slider φ ± π]      │ Quality: SNR [dB], error [%]│
├────────────────────────────────────────────────────────────┤
│ MULTI-CHANNEL DEMO                                         │
│ Ch1 (1 MHz): [message 1 plot]  → [demod output 1]         │
│ Ch2 (2 MHz): [message 2 plot]  → [demod output 2]         │
│ Ch3 (3 MHz): [message 3 plot]  → [demod output 3]         │
│ Select demod channel: [1] [2] [3]                          │
│ BPF selectivity: [slider wider/narrower]                   │
├────────────────────────────────────────────────────────────┤
│ [Sync tx/rx] [Add noise +6dB] [Induce phase error ±45°]  │
└────────────────────────────────────────────────────────────┘
```

### Key "Aha Moments"
1. **AM shifts spectrum by ωc.** Drag carrier frequency → watch spectrum shift left/right in real-time.
2. **FM expands bandwidth with modulation index.** Increase m → see sidebands spread (Carson's rule: BW ≈ 2(fm + Δf)). Understand why FM needs more spectrum but provides noise robustness.
3. **Synchronous demodulation requires phase lock.** Add phase error slider → signal fades (cos φ factor). See why carrier recovery is critical.
4. **Frequency-division multiplexing works because of spectral non-overlap.** Multiple channels coexist because their modulated spectra don't interfere if carriers are far apart.
5. **Envelope detection is simple but requires AM with carrier.** Toggle AM+C on → envelope detector works. Toggle it off → output is garbage. Shows why broadcast AM includes a carrier (power cost vs. simplicity).

### Technical Architecture
**Backend:**
- Receive: message signal m(t), modulation type, ωc, m (modulation index), receiver parameters (demod type, ωc_rx, φ error)
- Generate modulated signal:
  - AM: y(t) = m(t) · cos(ωct)
  - AM+C: y(t) = [m(t) + C] · cos(ωct)
  - PM: y(t) = cos(ωct + k·m(t))
  - FM: y(t) = cos(ωct + k·∫m(τ)dτ)
- Simulate demodulation:
  - Synchronous: z(t) = y(t) · cos(ωc_rx·t + φ), then LPF
  - Envelope: abs(y(t)) smoothed with lowpass
- Compute quality metrics: correlation with original m(t), MSE, SNR
- Return plots: message, modulated, received, demodulated, spectra, quality metrics

**Frontend:**
- Signal drawing canvas for message
- Modulation type buttons (radio buttons or dropdown)
- Sliders: ωc, m (mod index), receiver ωc, receiver phase error
- Real-time Plotly plots (time domain and frequency domain)
- Buttons: "Sync tx/rx", "Add noise", "Induce phase error"
- Multi-channel mode toggle + channel selector
- Audio playback of message vs. demodulated signal

**Complexity:** High. Requires phase modulation/demodulation, FM synthesis and demodulation (via frequency detection or discriminator), real-time spectrum computation, multi-channel signal mixing, quality metric calculation.

### Why This Isn't Generic
This is a **complete communication system simulator**, not a visualization. Students don't just see AM vs. FM—they **build transmitters and receivers, experience synchronization challenges, and design solutions**. It's a hands-on microlab for Lectures 23-24, with direct connection to real radio systems (AM/FM broadcast, multi-channel wireless).

---

## Tool 5: Sampling Rate Explorer with Spectral Folding
### Inspired By (Visual)
Lecture 21 extensively shows **spectral replication with different sampling rates** (sheets 27-48):
- Lower sampling rate → copies get closer together → aliasing becomes severe
- Anti-aliasing filter removes high frequencies before sampling
- Aliasing demonstration with music (sheet 49)

Lecture 25 mentions GPS, where sampling and signal processing are critical (though visual details are limited in contact sheets, the text emphasizes precision and modulation/demodulation).

### What Students DO (not watch)
- **Start with a signal** containing multiple frequency components (up to 200 kHz)
- **Slide sampling rate** from 10 kHz to 500 kHz and **watch spectral copies approach/overlap**
- **Predict aliasing** for selected frequency components (before simulation confirms)
- **Design anti-aliasing filter** by dragging LPF cutoff and watching high-frequency rejection
- **Compare audio quality** at different sampling rates (44.1 kHz, 48 kHz, 96 kHz, etc.)
- **Time-frequency explorer:** See how lower fs compresses the frequency axis (scale change Ω = ωT)

### Tool Description
A specialized **sampling-rate tuning environment** that emphasizes the relationship between fs and spectral replication. The core interaction: **dragging fs slider continuously shows spectral copies "moving" in real-time**, making the convolution-in-frequency mental model concrete.

Panels:
1. **Input spectrum:** User draws or selects multi-component signal
2. **Sampling impulse train in frequency:** Evenly spaced impulses at 0, ±fs, ±2fs, ... (spacing updates with fs)
3. **Output spectrum after convolution:** Automatic folding/aliasing visualization
4. **Optional: Anti-aliasing LPF** with draggable cutoff
5. **DTFT of samples:** Show how the output spectrum maps to DT frequency Ω ∈ [-π, π]

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────────┐
│  Sampling Rate Explorer                              │
├──────────────────────────────────────────────────────┤
│ Input Spectrum X(jω)                                 │
│ [0 to 250 kHz, draggable sinusoid markers]          │
│ ┌────────────────────────────────────────────────┐  │
│ │  │    │        │          │           │        │  │
│ │10k  30k     60k        100k         150k      │  │
│ └────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│ Sampling Impulse Train P(jω)                         │
│ Sampling rate: [slider] = 44.1 kHz  (edit box: Hz) │
│ ┌────────────────────────────────────────────────┐  │
│ │ ↑    ↑    ↑    ↑    ↑    ↑    ↑    ↑    ↑    │  │
│ │0   44.1  88.2 132.3 176.4 220.5 264.6 308.7  │  │
│ │        (spacing = fs)                        │  │
│ └────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│ Anti-Aliasing Filter (optional)                      │
│ ☑ Enable    Cutoff: [slider] kHz                    │
│ ┌────────────────────────────────────────────────┐  │
│ │ ━━━━━━━┐                                       │  │
│ │        └──────────────────────                 │  │
│ └────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│ Output Spectrum after Sampling (& optional LPF)      │
│ [Shows folding; aliases in red/warning color]       │
│ ┌────────────────────────────────────────────────┐  │
│ │  │    │        │    │ RED │         │        │  │
│ │10k  30k     60k   44k  RED 100k→-16k 150k    │  │
│ │                    ↓ aliased               │  │
│ └────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│ DT Fourier Transform (frequency scale Ω = ωT)        │
│ ┌────────────────────────────────────────────────┐  │
│ │  │ RED │    │        │           │            │  │
│ │-π         -π/2      0         π/2         π  │  │
│ │      Ω = ωT = 2π(ω/fs)                      │  │
│ └────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│ Nyquist Frequency: ωs/2 = [auto-computed] kHz       │
│ Aliased Components: [list with predictions]         │
│ Audio: [Play at 44.1 kHz] [Play at 8 kHz]          │
└──────────────────────────────────────────────────────┘
```

### Key "Aha Moments"
1. **Spectral copies move with fs.** Drag the sampling rate slider → see the impulse train spacing change → copies approach each other → aliasing becomes visible as overlap.
2. **Nyquist is a hard boundary.** Anything above fs/2 folds back. Interactive folding map shows this geometry.
3. **Anti-aliasing filter prevents aliasing by stopping high frequencies before they replicate.** Turn the LPF on → watch the input spectrum get truncated → aliases disappear.
4. **Scale change Ω = ωT is not abstract.** Watch the output spectrum compress/expand as you change fs; the DTFT panel shows how ω maps to Ω.
5. **Different sampling rates are different trade-offs.** 8 kHz sounds terrible (music aliasing), 44.1 kHz sounds good (CD quality), 96 kHz sounds the same as 44.1 kHz to human ear (but has advantages for processing).

### Technical Architecture
**Backend:**
- Input: signal x(t) (as spectrum or parametric), fs, LPF cutoff ωc (optional)
- Compute impulse train P(jω) at multiples of fs
- Convolve X(jω) * P(jω) (or equivalently, create copies of X and sum at ±kfs)
- Apply optional LPF
- Identify aliased components (frequencies >fs/2 that wrap into [-fs/2, fs/2])
- Return: input spectrum, impulse train, LPF, output spectrum, aliasing list

**Frontend:**
- Multi-panel layout with synchronized frequency axes
- Continuous fs slider (10 kHz to 500 kHz); changes update all plots in real-time
- LPF cutoff slider with toggle
- Drag-to-place sinusoid markers on input spectrum
- Highlighted/colored regions showing aliased components
- Audio playback at selected fs (Web Audio)
- Read-out of Nyquist frequency, fs, cutoff

**Complexity:** Medium. Requires accurate spectral convolution, careful axis scaling and synchronization, real-time audio synthesis at different sample rates.

### Why This Isn't Generic
This tool makes the **convolution-in-frequency operation visual and interactive**. Students don't learn "aliasing happens when fs < 2W"; they see spectral copies approach and overlap as they drag a slider. It directly reinforces Lecture 21's core insight: sampling creates periodic spectral copies, and Nyquist prevents their overlap.

---

## Tool 6: CD Audio Processing Pipeline (System Integration)
### Inspired By (Visual)
Lecture 25 "From LPs to CDs" shows the **complete AD/DA chain for audio**:
- Anti-aliasing filter + sampling at 44.1 kHz (sheets 17-18)
- Quantization to 16 bits (sheet 13)
- Downsampling to CD rate (sheets 30-34)
- Reconstruction (upsampling) when playing (sheets 34+)
- CD physical structure and pit/land encoding (sheets 12-14)
- Laser interferometry and feedback control (sheets 38-72)

### What Students DO (not watch)
- **Record audio:** Upload or record live voice; observe real-time spectral analysis
- **Design ADC filter chain:** Adjust anti-aliasing filter cutoff, observe frequency response
- **Choose sampling rate:** 44.1 kHz, 48 kHz, 96 kHz; see resulting file size and quality trade-off
- **Quantize to 16 bits:** See amplitude quantization, hear quantization noise
- **Engineer playback:** Design reconstruction filter, observe sinc interpolation
- **Measure quality metrics:** SNR, frequency response, Total Harmonic Distortion (THD)
- **End-to-end challenge:** "Record, encode, and play back a vocal sample with minimal artifacts"

### Tool Description
A **complete audio engineering simulator** that chains all the concepts from Lectures 19-25 into one coherent system. Students see how theoretical concepts (sampling, quantization, filtering, signal reconstruction) combine to create the multi-billion-dollar CD industry.

The tool has three main pages:
1. **Recording side (ADC):** Input signal → Anti-aliasing filter → Sampler → Quantizer → Output data
2. **Playback side (DAC):** Stored data → Upsampler → Reconstruction filter → Output signal
3. **Quality & Comparison:** SNR, frequency response, spectrogram, before/after plots, predicted file size

### Multi-Panel Layout
```
┌──────────────────────────────────────────────────────────┐
│  CD Audio Processing Pipeline                            │
├──────────────────────────────────────────────────────────┤
│ [RECORD SIDE] – Analog-to-Digital                        │
├──────────────────────────────────────────────────────────┤
│ Input Signal                │ After Anti-Aliasing Filter │
│ [upload or record]          │ (cutoff: [slider] kHz)     │
│ [time plot 0-1s]            │ [magnitude response]        │
│ [spectrum 0-100kHz]         │ [filtered signal]           │
├─────────────────────────────┼────────────────────────────┤
│ Sampling at fs = [44.1] kHz │ Quantization: 16 bits      │
│ [impulse samples]           │ [quantized waveform]       │
│ [spectrum post-sampling]    │ [error signal]             │
├──────────────────────────────────────────────────────────┤
│ File Size Estimate: 44100 × 2 bytes × 60s = 5.3 MB      │
├──────────────────────────────────────────────────────────┤
│ [PLAYBACK SIDE] – Digital-to-Analog                      │
├──────────────────────────────────────────────────────────┤
│ Upsampling 4× (↑4)          │ Reconstruction Filter      │
│ [zero-insertion visible]    │ (cutoff: [slider] kHz)     │
│                             │ [magnitude response]        │
├─────────────────────────────┼────────────────────────────┤
│ After Upsampling            │ Reconstructed Output       │
│ [spectrum shows copies]     │ [time plot]                │
│                             │ [spectrum compare to orig] │
├──────────────────────────────────────────────────────────┤
│ [QUALITY METRICS]                                        │
│ SNR: [computed]       THD: [%]       Correlation: [%]   │
│ [Frequency response plot: input vs. output magnitude]    │
│ [Spectrogram: time-frequency energy, original vs. output]│
├──────────────────────────────────────────────────────────┤
│ [Play original] [Play after 16-bit quantization]         │
│ [Play reconstructed] [A/B comparison slider]             │
└──────────────────────────────────────────────────────────┘
```

### Key "Aha Moments"
1. **Sampling + filtering work together.** Remove both anti-aliasing and reconstruction filters → severe artifacts. Include them → high fidelity.
2. **44.1 kHz is engineered, not arbitrary.** Designed to fit CD specs (74-minute audio ≈ 650 MB), preserve audible bandwidth (20 kHz), and allow room for anti-aliasing filter transition.
3. **16 bits is sufficient for 96 dB SNR.** More than human hearing can distinguish in most listening environments.
4. **Downsampling/upsampling trade bandwidth for lower file size.** Downsample to 22 kHz, then upsample to 44.1 kHz for playback; saves space but loses high frequencies.
5. **Real audio engineering is iterative.** Choose filter cutoff, measure SNR, adjust, repeat. This tool lets students do that optimization loop.

### Technical Architecture
**Backend:**
- Accept input signal (audio file or parametric)
- ADC chain:
  - Apply LPF with user-chosen cutoff (compute IIR or FIR response)
  - Sample at fs (interpolate/evaluate at sample times)
  - Quantize to B bits
- DAC chain:
  - Upsample by factor L (insert L-1 zeros between samples)
  - Apply LPF reconstruction filter
  - Optionally resample to output rate (e.g., 96 kHz)
- Quality metrics:
  - SNR = 10 log10(P_signal / P_error)
  - Correlation with original (normalized)
  - Frequency response: magnitude of FFT(output) / FFT(input)
  - THD (harmonic distortion) from quantization
  - Estimated file size: fs × bits × duration

**Frontend:**
- Upload or microphone input for recording
- LPF cutoff sliders (record side, playback side)
- Quantization bit-depth selector (8, 12, 16, 24 bits)
- Upsampling factor selector (1, 2, 4)
- Multiple synchronized plots (time, frequency, spectrogram)
- Quality metrics display (numerical + graphical)
- A/B audio comparison (slider to blend original/output)
- File size calculator

**Complexity:** Very High. Requires audio file I/O, real-time FFT and STFT for spectrograms, FIR/IIR filter design, upsampling/downsampling with anti-imaging filters, quality metric computation, audio playback synchronization.

### Why This Isn't Generic
This is a **professional-grade audio engineering tool**, not a toy simulator. It connects 6 lectures of theory (Fourier relations, sampling, quantization, filtering, modulation) into one coherent workflow. Students don't just learn *about* CDs; they **engineer an audio codec from first principles**. It's the capstone tool for Lectures 19-25.

---

## Summary Table

| Tool | Core Concept | Interaction Model | Complexity | Key Innovation |
|------|--------------|------------------|------------|-----------------|
| **Fourier Domain Navigator** | Four Fourier representations as unified view | Drag signal between domains; all four update | Medium | Unified transform visualization; sampling/periodicity duality |
| **Aliasing Discovery Lab** | Aliasing via spectral wrapping | Compose frequencies; drag fs; predict→verify | Medium-High | Real-time frequency folding map; audio playback of aliases |
| **Sampling & Reconstruction Pipeline** | Complete AD/DA chain | Draw signal; adjust fs, LPF, bit depth | High | Visible impulse samples, sinc interpolation, quantization levels |
| **Modulation & Demodulation Studio** | AM/PM/FM and receiver design | Build transmitter/receiver; tune parameters | High | Live spectrum shift; phase lock challenges; multi-channel FDM |
| **Sampling Rate Explorer** | Spectral replication and aliasing geometry | Drag fs slider; watch spectral copies move | Medium | Convolution-in-frequency made visual; continuous fs tuning |
| **CD Audio Pipeline** | Integration of all concepts into real system | Record → filter → sample → quantize → play | Very High | Professional audio workflow; complete engineering loop |

---

## Design Principles (All Tools)

1. **Make invisible operations visible.** Every step (sampling, filtering, modulation, quantization) has a real-time plot or waveform view.

2. **Prediction → Verification loop.** Students predict outcomes before seeing results (e.g., "Will 100 kHz alias to 22 kHz at 44 kHz sampling?"). Immediate feedback builds intuition.

3. **Live parameter exploration.** Drag sliders continuously to see effects unfold in real-time, not discrete "run simulation" steps.

4. **Multi-domain visualization.** Time-domain plots alongside frequency-domain plots. Students learn to think in both domains simultaneously.

5. **Audio playback** (where applicable). Hearing aliasing, quantization noise, and modulation effects is more memorable than seeing plots.

6. **Error metrics and quality assessment.** SNR, MSE, correlation, etc. Let students measure trade-offs quantitatively.

7. **Connection to real-world applications.** Every tool references a real system: radios (modulation), CDs (sampling/quantization), radio receivers (FDM), microphones (filtering), etc.

8. **Build systems, not just adjust parameters.** Students compose transmitters, design filters, and build pipelines—not just watch animations.

---

## Existing Simulations NOT to Duplicate

Tools listed as existing in the project: aliasing_quantization, sampling_reconstruction, modulation_techniques (and others). These 6 tools expand on those foundations with **interaction models that require construction and prediction**, not just parameter variation. Each tool is a **mini-Simulink** where students build systems and discover relationships through hands-on exploration.

---

## Notes for Implementation

- **Leverage existing** rc_lowpass_filter, signal_parser, fourier_series, and block_diagram_builder patterns
- **Custom viewers** needed for: spectral folding visualization, multi-panel synchronized plots, draggable frequency markers
- **Audio playback** requires Web Audio API integration (beyond standard Plotly)
- **Performance:** FFT/STFT computations may need NumPy/SciPy backend with caching for real-time sliders
- **Mobile responsiveness:** Multi-panel layouts should stack or compress gracefully on small screens
