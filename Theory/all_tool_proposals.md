# All Tool Proposals — MIT 6.003 Lecture Analysis

105 unique simulation/tool proposals across 25 lectures, deduplicated against 44 existing simulations.

---

## Lecture 1: Signals and Systems (Abstraction & Fundamentals)

1. **Leaky Tank Simulator** (`leaky_tank`) — Animated first-order CT system (water tank) with adjustable time constant, input profiles, and capacitor circuit analogy
2. **Signal Transformation Playground 2D** (`signal_transform_2d`) — Apply mathematical transformations to 2D images (scale, shift, reflect), with quiz mode mirroring the Stata Center exercise
3. **Reconstruction Method Comparator** (`reconstruction_methods`) — Compare zero-order hold, first-order hold, and ideal sinc interpolation for reconstructing CT signals from DT samples
4. **Time Constant Explorer** (`time_constant_explorer`) — Interactive exploration of how tau affects step response across multiple physical analogies (tank, RC circuit, thermal system)
5. **System Cascade / Series Composition Lab** (`system_composition`) — Drag first-order blocks to wire cascade, parallel, and feedback configurations; auto-compute composite system properties

---

## Lecture 2: Discrete-Time Systems

6. **DT Step-by-Step Block Diagram Solver** (`dt_step_solver`) — Animate sample-by-sample computation through block diagrams, showing values at every wire, delay register, and adder at each clock tick
7. **Operator Equivalence Checker** (`operator_equivalence`) — Enter two operator expressions or block diagrams, verify algebraic equivalence step-by-step with highlighted properties (commutative, distributive, associative)
8. **Accumulator & Difference Machine Duality** (`accumulator_differencer`) — Side-by-side comparison of the IIR accumulator 1/(1-R) and the FIR differencer (1-R), demonstrating they are operator inverses
9. **Synthetic Division / Long Division Visualizer** (`long_division_series`) — Step-by-step long division on H(R) = N(R)/D(R) to generate impulse response coefficients h[0], h[1], h[2]...

---

## Lecture 3: Feedback, Poles, and Fundamental Modes

10. **Fibonacci System Explorer** (`fibonacci_system`) — Explore the Fibonacci recurrence as a signals & systems problem with golden ratio poles, mode decomposition, and closed-form vs iterative comparison
11. **Partial Fraction Decomposition Visualizer** (`partial_fractions`) — Enter H(R) or H(z) as polynomial ratio, see step-by-step PFD, parallel block diagram, and per-mode impulse response contributions
12. **Four Regimes of Real Poles DT** (`dt_pole_regimes`) — Drag a pole along the real number line and watch the impulse response change across all four regimes (diverge+alternate, converge+alternate, converge+monotone, diverge+monotone)
13. **Complex Pole Phasor Animation** (`complex_phasor_animation`) — Animate rotating phasor on the complex plane for complex conjugate poles, showing real/imaginary parts as sinusoidal DT stem plots
14. **Polynomial Multiplication Table Visualizer** (`poly_mult_table`) — Tabular multiplication of power series with highlighted reverse diagonals, showing cascade system impulse response construction

---

## Lecture 4: Continuous-Time Systems

15. **CT Feedback Cycle Visualizer** (`ct_operator_series`) — Show how CT feedback builds e^(pt) term-by-term via successive integrations (Taylor series), with partial sums converging to exponential
16. **Mass-Spring Sinusoidal Mode Builder** (`mass_spring_series`) — Animate operator series expansion converging to omega_0*sin(omega_0*t) for the mass-spring system
17. **CT vs DT Stability Regions Comparator** (`stability_regions`) — Side-by-side s-plane and z-plane with shaded stability regions, pole placement, and cross-domain discretization mapping
18. **CT Impulse as Limit Visualizer** (`impulse_limit_lab`) — Animate delta(t) construction as rectangular pulses shrink in width and grow in height while maintaining unit area

---

## Lecture 5: Z Transform

19. **DT Concept Map Navigator** (`dt_concept_map`) — Enter any one of five DT representations (block diagram, system functional, difference equation, system function, unit-sample response) and auto-derive all others
20. **Z Transform ROC & Causality Explorer** (`z_roc_causality`) — Click different ROC regions on the z-plane to see how the same H(z) maps to different time-domain signals (causal vs anti-causal)

---

## Lecture 6: Laplace Transform

21. **CT Representation Navigator** (`ct_representation_navigator`) — Enter a CT system in any of five representations and auto-compute all others simultaneously, with clickable arrows showing conversion steps
22. **Partial Fraction Decomposition Workbench** (`partial_fraction_workbench`) — Step-by-step partial fraction expansion of H(s) with selectable ROCs per pole, showing how the same expression yields different time-domain signals
23. **Laplace Transform ODE Solver Step-by-Step** (`laplace_ode_step_solver`) — Walk through the four-step Laplace ODE solution process with full KaTeX algebra at each stage

---

## Lecture 7: Discrete Approximation of CT Systems

24. **Discretization Method Comparator** (`discretization_comparator`) — Apply Forward Euler, Backward Euler, and Bilinear Transform to the same CT system, overlay DT responses against true CT, show stability behavior
25. **s-to-z Mapping Visualizer** (`s_to_z_mapping`) — Interactive dual-pane tool where users select s-plane regions and watch them morph into z-plane under each discretization mapping
26. **Leaky Tank Simulator** (`leaky_tank`) — Interactive leaky tank with physical animation, CT vs DT solution comparison, and adjustable time constant/sampling period

---

## Lecture 8: Convolution

27. **Superposition Decomposition Visualizer** (`superposition_decomposer`) — Decompose input into individual impulse components, show each weighted/shifted impulse response, and animate their summation into total output
28. **Optical PSF & Deconvolution Explorer** (`optical_psf_deconvolution`) — Apply Gaussian/Airy-disk PSF blur to images, simulate Hubble cascade blur, and attempt Wiener deconvolution
29. **CT Convolution Integral Visualizer** (`ct_convolution_integral`) — Animated flip-shift-multiply-integrate for CT convolution with shaded integral area building up as t sweeps
30. **DT Step-by-Step System Solver** (`dt_step_solver`) — Step through DT system computation sample-by-sample with live values on block diagram nodes

---

## Lecture 9: Frequency Response

31. **LTI Eigenfunction Explorer** (`lti_eigenfunction_explorer`) — Test multiple candidate input functions (e^st, cos, u(t)) to discover which are eigenfunctions of a given LTI system
32. **Conjugate Symmetry & Frequency Response Calculator** (`conjugate_symmetry_freq`) — Decompose cos(w0*t) into complex exponentials, compute H(jw0) eigenvalues, show conjugate pair combining to produce real output
33. **Mass-Spring-Dashpot Frequency Response Demo** (`msd_frequency_response`) — Animated driven oscillator with frequency sweep, Bode plots annotating w0/w_d/w_peak distinctions, and vector diagram

---

## Lecture 10: Feedback and Control

34. **WallFinder Proportional Control Simulator** (`wallfinder_control`) — Interactive robot-approaching-wall with proportional gain K, space-time diagram, z-plane poles, and three response regimes including deadbeat
35. **Root Locus Gain Sweep Explorer** (`root_locus_gain_sweep`) — Sweep gain K and trace animated root locus showing poles migrating, with synchronized step response updates
36. **Feedback Delay Destabilizer** (`feedback_delay_demo`) — Side-by-side comparison of 0, 1, 2, 3 delay steps showing how delay limits achievable performance and shrinks stable gain range
37. **Aerodynamic Coefficient Explorer** (`aero_coefficient_explorer`) — System identification from real glider flight data: fit lift/drag coefficients vs angle of attack
38. **Proportional Gain Pole Placement Workbench** (`proportional_pole_placement`) — Focused tool for choosing proportional gain K with regime labels, deadbeat indicator, and root locus trace

---

## Lecture 11: CT Frequency Response and Bode Plots

39. **Bode Plot Builder** (`bode_plot_builder`) — Place poles/zeros on s-plane; decompose H(s) into individual factor contributions; overlay exact and asymptotic Bode curves with error annotations
40. **Bode Plot Identification Quiz** (`bode_identification`) — Present Bode plots and challenge users to identify the transfer function from multiple choices, with decomposition reveal
41. **High-Q Bandwidth Analyzer** (`high_q_bandwidth`) — Adjust Q and omega_0 for second-order systems; show peaked magnitude growing to Q, bandwidth narrowing to omega_0/Q, vectorial analysis from poles

---

## Lecture 12: CT Feedback and Control (Part 1)

42. **Gain-Bandwidth Tradeoff Explorer** (`gain_bandwidth_tradeoff`) — Op-amp feedback with adjustable beta, showing gain-bandwidth product conservation, pole movement, step response speedup
43. **Root Locus Animator** (`root_locus_animator`) — Trace root locus as amplifier gain varies; show pole collision, complex splitting, and overdamped-to-underdamped transition with step response

---

## Lecture 13: CT Feedback and Control (Part 2)

44. **Crossover Distortion Simulator** (`crossover_distortion`) — Push-pull amplifier with deadzone; apply feedback to progressively reduce distortion; show FFT and THD metrics
45. **Magnetic Levitation Stabilizer** (`magnetic_levitation`) — Stabilize inherently unstable maglev system (RHP poles) using outer feedback loop with compensator; animated root locus showing pole migration to LHP
46. **Sensitivity Reduction via Feedback** (`sensitivity_feedback`) — Show how overall gain becomes insensitive to plant gain variation as loop gain increases, with sensitivity metric computation
47. **Inverted Pendulum Stabilizer** (`inverted_pendulum_stabilizer`) — 2D pendulum-on-cart with PD/PID controller design, root locus, and animated stabilization

---

## Lecture 14: Fourier Representations

48. **Gibbs Phenomenon Explorer** (`gibbs_convergence`) — The persistent ~9% overshoot at discontinuities of a truncated Fourier series that does not vanish as N increases; convergence rate (1/k vs 1/k^2) determines whether ringing appears
49. **Harmonic Timbre Synthesizer** (`harmonic_timbre`) — Different instruments playing the same note produce different waveforms because of different harmonic amplitude profiles (timbre); consonance/dissonance determined by harmonic overlap
50. **Spectral Filter Workbench** (`spectral_filter_workbench`) — An LTI system acts as a frequency selector: it cannot create new frequencies, only scale and phase-shift existing harmonics. Shows four regimes of passing a square wave through an RC lowpass filter
51. **Fourier Analysis & Synthesis Lab** (`fourier_analysis_lab`) — Derives the analysis equation a_k = (1/T) integral of x(t)e^{-jkw_0t} dt from orthogonality; computes square wave coefficients; demonstrates the differentiation property
52. **Musical Harmonics and Consonance Explorer** (`harmonics_consonance`) — Musical timbre as harmonic content; consonance/dissonance determined by harmonic alignment between notes
53. **Fourier Coefficient Calculator** (`fourier_coefficient_calc`) — Computing Fourier series coefficients via the analysis integral step by step, showing the integrand for each k and the resulting a_k

---

## Lecture 15: Fourier Series

54. **Orthogonal Decomposition Lab** (`orthogonal_decomposition`) — The Fourier series analysis equation extracts harmonic coefficients via the inner product, exactly analogous to projecting a 3D vector onto basis vectors via dot products
55. **Parseval's Energy Analyzer** (`parseval_energy`) — Parseval's theorem: total energy computed in the time domain equals the sum of squared magnitudes of the Fourier coefficients
56. **Source-Filter Vowel Synthesizer** (`source_filter_speech`) — Speech is produced by a periodic glottal source (buzz from vocal cords) filtered by the vocal tract transfer function H(jw); formants shape vowel sounds
57. **Frequency-Domain Filtering Workbench** (`freq_domain_filter`) — An LTI system filters a signal by multiplying its Fourier transform by the system's frequency response: Y(jw) = H(jw) * X(jw)
58. **Fourier Orthogonality Visualizer** (`fourier_orthogonality`) — Fourier analysis as orthogonal decomposition; the inner product (integral over a period) extracts individual harmonic coefficients

---

## Lecture 16: Fourier Transform

59. **Series-to-Transform Limit Visualizer** (`series_to_transform`) — The Fourier transform arises as the limit of Fourier series coefficients as the period T approaches infinity
60. **Fourier Transform Duality Explorer** (`fourier_duality`) — The Fourier transform and its inverse differ only by a sign flip and a 2pi scaling factor; duality principle demonstration
61. **Time-Frequency Scaling & Uncertainty Lab** (`time_freq_scaling`) — When a signal is scaled in time by a factor a, its Fourier transform becomes (1/|a|)*X(jw/a); time compression leads to frequency expansion and vice versa
62. **Ideal Low-Pass Filter & Inverse FT Synthesizer** (`ideal_filter_synthesis`) — The inverse Fourier transform enables computing the time-domain impulse response of an ideal filter directly from its frequency-domain specification
63. **Laplace-to-Fourier Slice Visualizer** (`laplace_fourier_slice`) — The Fourier transform is the Laplace transform evaluated on the jw axis: X(jw) = X(s)|_{s=jw}. 3D surface visualization
64. **CT Fourier Transform Explorer** (`ct_fourier_transform`) — CT Fourier Transform analysis/synthesis equations, and how time-domain signal shape maps to frequency-domain spectrum shape

---

## Lecture 17: DT Frequency Representations

65. **DT Frequency Aliasing Explorer** (`dt_frequency_aliasing`) — DT frequency responses are periodic in 2pi; e^{jOmega} is periodic in Omega; the "highest" DT frequency is at Omega = pi
66. **DT Vector Diagram Frequency Response Builder** (`dt_vector_freq_response`) — Constructing the DT frequency response H(e^{jOmega}) by evaluating H(z) on the unit circle using vector diagrams from poles and zeros
67. **DT Fourier Series Matrix Lab** (`dt_fourier_series_matrix`) — DT Fourier series as a finite matrix decomposition (the DFT matrix)
68. **Speaker Equalization & DT Filter Design** (`speaker_equalizer`) — Loudspeaker frequency response compensation as a real-world motivation for DT signal processing
69. **DT Filter Type Classifier** (`dt_filter_classifier`) — Given a pole-zero configuration in the z-plane, determine the filter type: lowpass, highpass, bandpass, or bandstop (notch)
70. **DT Frequency Response from Pole-Zero** (`dt_freq_response_pz`) — Computing DT frequency response H(e^{jOmega}) by evaluating H(z) on the unit circle, using vector diagrams
71. **DT Aliasing Visualizer** (`dt_aliasing`) — DT frequency periodicity (period 2pi), aliasing, and the concept that Omega=pi is the highest DT frequency
72. **DT Fourier Series Matrix Visualizer** (`dt_fourier_matrix`) — DT Fourier Series as an N x N matrix multiplication (the DFT matrix), and its inverse

---

## Lecture 18: DT Fourier Representations

73. **All-Pass Filter Phase Explorer** (`allpass_phase_explorer`) — The DT all-pass filter H(z) = (1 - a*z)/(z - a) has unit magnitude for all Omega, yet its nontrivial phase response profoundly changes signal shape
74. **DT Fourier Series Matrix & FFT Visualizer** (`dtfs_fft_visualizer`) — The DT Fourier Series expressed as a matrix multiply between a DFT matrix (twiddle factors W_N^{kn}) and the signal vector
75. **DTFT from Periodic Extension Demonstrator** (`dtft_periodic_extension`) — The DTFT is derived by taking a finite-length signal, periodically extending it with period N, computing the N-point DTFS, and letting N -> infinity
76. **2D Image Fourier Magnitude-Phase Decomposition Lab** (`image_fourier_magphase`) — The 2D DFT of an image decomposed into magnitude and phase components; demonstrates that phase carries structural information
77. **DTFT Properties Workbench** (`dtft_properties_workbench`) — The DTFT inherits all properties of the Z-transform (linearity, time shift, multiply-by-n, convolution), evaluated on the unit circle
78. **FFT Butterfly Diagram Visualizer** (`fft_butterfly`) — The Cooley-Tukey FFT algorithm: divide-and-conquer decomposition of an N-point DFT into smaller DFTs with butterfly operations
79. **DT Fourier Transform (DTFT) Explorer** (`dtft_explorer`) — The DTFT X(e^{jOmega}) = sum of x[n]e^{-jOmega*n}: a continuous, 2pi-periodic function computed from a discrete-time signal

---

## Lecture 19: Relations among Fourier Representations

80. **Fourier Representation Navigator** (`fourier_representation_navigator`) — The four Fourier representations (CTFS, CTFT, DTFS, DTFT) are a single unified framework connected by four operations: sampling, interpolation, periodic extension, and limiting
81. **Periodic Extension & Frequency Sampling Lab** (`periodic_extension_lab`) — When an aperiodic signal is periodically extended, its frequency representation changes from a continuous spectrum to a discrete set of impulses at harmonics
82. **Time-Frequency Duality Sandbox** (`time_freq_duality`) — The fundamental time-frequency duality in a 2x2 matrix: discrete vs. continuous crossed with periodic vs. aperiodic
83. **CT-to-DT Sampling Spectrum Visualizer** (`ct_dt_sampling_spectrum`) — When a CT signal x(t) is sampled at interval T, the resulting DT Fourier transform X(e^{jOmega}) is a periodized and frequency-scaled version of the CT Fourier transform
84. **Four Fourier Representations Navigator** (`fourier_representations`) — The relationships among CTFS, CTFT, DTFS, DTFT: sampling in time causes replication in frequency; periodic extension in time causes sampling in frequency
85. **Sampling & Spectrum Replication** (`sampling_spectrum`) — Sampling a CT signal at rate 1/T replicates X(jw) at intervals of 2pi/T in the frequency domain

---

## Lecture 20: Applications of Fourier Transforms

86. **ECG Noise Filter Designer** (`ecg_filter_designer`) — Composite filter design (HPF + LPF + notch) applied to a realistic noisy biomedical signal
87. **Diffraction Grating & Fourier Transform Simulator** (`diffraction_fourier`) — The far-field diffraction pattern of a periodic structure is the Fourier transform of that structure's spatial profile
88. **Frequency-Domain Filtering Workbench** (`freq_domain_filter`) — An LTI system filters a signal by multiplying its Fourier transform by the system's frequency response: Y(jw) = H(jw) * X(jw)
89. **2D Fourier Transform & Crystallography Lab** (`crystallography_ft`) — X-ray crystallography produces images that are the 2D Fourier transform of molecular structure (Rosalind Franklin's Photo 51)
90. **Spectral Filtering Lab** (`spectral_filtering`) — Fourier analysis for filter design: identifying noise in the frequency domain and designing filters (LPF + HPF + notch) to remove it
91. **Lowpass Filtering of Square Waves** (`lpf_square_wave`) — Passing a square wave through an RC lowpass filter at different relative frequencies, showing how harmonics above the cutoff are attenuated

---

## Lecture 21: Sampling

92. **Spectral Replication Visualizer** (`spectral_replication`) — When a CT signal is multiplied by an impulse train with period T, the resulting spectrum is a convolution in frequency that produces infinitely many spectral copies
93. **Frequency Wrapping Explorer** (`frequency_wrapping`) — Aliasing causes deterministic frequency wrapping: any input frequency f_in maps to an aliased frequency f_out via a zigzag/sawtooth function
94. **2D Image Sampling & Moire Pattern Lab** (`image_sampling_2d`) — Sampling applies in 2D just as in 1D; demonstrates Moire patterns from undersampled images
95. **Anti-Aliasing Filter Pipeline Simulator** (`antialiasing_pipeline`) — The full sampling-and-reconstruction pipeline: anti-aliasing LPF before sampling, impulse train multiplication, and reconstruction filtering
96. **CTFT-DTFT Frequency Scaling Bridge** (`ctft_dtft_bridge`) — The DTFT X(e^{jOmega}) and the CTFT Xp(jw) are related by the frequency scaling Omega = wT

---

## Lecture 22: Sampling and Quantization

97. **DT Resampling & Rate Conversion Lab** (`dt_resampling`) — Discrete-time sampling rate conversion: decimation, interpolation, and rational rate conversion
98. **Sigma-Delta Noise Shaping Modulator** (`sigma_delta_modulator`) — Oversampling, noise shaping, and sigma-delta (delta-sigma) modulation
99. **DCT-Based Perceptual Compression Explorer** (`dct_compression`) — Discrete Cosine Transform, perceptual quantization, and JPEG-like compression pipeline
100. **Quantization Noise Spectrum Analyzer** (`quantization_noise`) — Quantization error statistics, noise floor, and the 6.02 dB/bit rule
101. **Fourier Series vs DCT Comparison** (`fs_dct_comparison`) — Why the DCT produces smaller high-frequency coefficients than the Fourier series: the symmetric periodic extension avoids discontinuities at block boundaries

---

## Lecture 23: Modulation Part 1 (AM)

102. **Synchronous Demodulation Phase Sensitivity Explorer** (`sync_demod_phase`) — When a demodulator's local oscillator has a phase offset phi, the recovered signal becomes (1/2)x(t)cos(phi), showing why phase-lock is critical
103. **Superheterodyne Receiver Simulator** (`superheterodyne_rx`) — The superheterodyne architecture: coarse tunable BPF, mixer to fixed IF, high-quality IF filter for selectivity
104. **Bandpass Filter Equivalence Lab** (`bandpass_equivalence`) — Three different system architectures that may or may not implement a bandpass filter; quiz-style exploration
105. **AM Power Budget & Crest Factor Analyzer** (`am_power_budget`) — The power cost of AM-with-carrier: most transmit power goes to the carrier, not the information-bearing sidebands
106. **Frequency-Division Multiplexing Visualizer** (`fdm_visualizer`) — How multiple signals share a single transmission medium by occupying non-overlapping frequency bands
107. **Envelope Detector / Peak Detector Circuit Simulator** (`envelope_detector`) — How an AM signal with a DC carrier offset can be demodulated using a simple RC peak detector circuit

---

## Lecture 24: Modulation Part 2 (FM)

108. **Bessel Spectrum Explorer** (`bessel_spectrum`) — What the Fourier transform of a PM/FM signal looks like: y(t) = cos(wc*t + m*sin(wm*t)) decomposed via Bessel functions of the first kind
109. **Superheterodyne Receiver Simulator** (`superheterodyne_receiver`) — The superheterodyne architecture applied to FM: coarse tunable BPF, mixer to fixed IF, discriminator for FM demodulation
110. **Narrowband FM Bandwidth Paradox** (`narrowband_fm_paradox`) — Debunks the misconception that reducing the FM modulation index to near zero produces arbitrarily narrow bandwidth; proves NB-FM bandwidth equals AM bandwidth
111. **Structured Illumination Microscopy** (`structured_illumination`) — Modulation theory applied to microscopy: a sinusoidal illumination pattern shifts high-frequency spatial content into the passband of the microscope objective
112. **FM Bessel Spectrum Analyzer** (`fm_bessel`) — How FM modulation with a sinusoidal message produces a spectrum whose coefficients are Bessel functions; increasing modulation index m spreads energy across more sidebands
113. **Narrowband vs Wideband FM Comparator** (`nb_wb_fm`) — The misconception that narrowband FM can have arbitrarily narrow bandwidth, and the proof that as k approaches 0, FM bandwidth equals AM bandwidth

---

## Lecture 25: From LPs to CDs

114. **Oversampling & Anti-Aliasing Filter Relaxation Explorer** (`oversampling_filter`) — Sampling at M times the Nyquist rate creates a large spectral gap between the signal band and the first alias, relaxing anti-aliasing filter requirements
115. **CD Interferometric Pit Reader Simulator** (`cd_pit_reader`) — A CD stores data as physical pits (0.5 um deep, 0.83-3.56 um long) and lands on a reflective surface; laser interferometry reads them
116. **Quadrant Detector Focusing Feedback Simulator** (`cd_servo_feedback`) — A CD player uses two nested feedback control loops: focus servo (astigmatic lens method with quadrant detector) and tracking servo
117. **Multirate Signal Processing Pipeline** (`multirate_dsp`) — The CD system uses multirate signal processing: sampling rate conversion via integer-factor upsampling and downsampling with appropriate filtering
118. **CD Audio Pipeline Simulator** (`cd_audio_pipeline`) — The complete end-to-end digital audio pipeline: sampling, filtering, oversampling, downsampling, and reconstruction as an integrated system
119. **Oversampling Filter Design Workbench** (`oversampling_design`) — How oversampling relaxes the anti-aliasing filter by widening the transition band, allowing a lower-order analog filter

---

## Cross-Lecture Tools (not tied to a single lecture)

120. **Nyquist Plot & Stability Criterion** (`nyquist_stability`) — Map open-loop frequency response on Nyquist diagram, count encirclements of -1+j0
121. **Gain & Phase Margin Analyzer** (`gain_phase_margin`) — Compute and display GM/PM on Bode plots with color-coded stability zones
122. **Lead-Lag Compensator Designer** (`lead_lag_compensator`) — Add lead/lag compensators interactively, see Bode/root locus/step response modifications
123. **PID Tuning Lab** (`pid_tuning_lab`) — Interactive PID tuning with Ziegler-Nichols auto-tune, performance metrics, and comparison of P/PI/PD/PID
124. **LQR Designer** (`lqr_designer`) — State-space LQR design with Q/R weight adjustment, optimal gain computation, and comparison vs PID
125. **Transfer Function to State Space Converter** (`tf_ss_converter`) — Convert between TF and state-space (controller canonical, observer canonical, Jordan form)
126. **Controllability & Observability Analyzer** (`controllability_observability`) — Compute controllability/observability matrices, check rank, Kalman decomposition
127. **Steady-State Error Analyzer** (`steady_state_error`) — Determine system type, compute Kp/Kv/Ka error constants, show error for step/ramp/parabolic inputs
128. **Routh-Hurwitz Stability Criterion Tool** (`routh_hurwitz`) — Build Routh array step-by-step, highlight sign changes, determine stability range for parametric K
129. **Convolution Theorem Demonstrator** (`convolution_theorem`) — Side-by-side time-domain convolution animation and frequency-domain spectrum multiplication
130. **Cross-Domain Analogizer** (`cross_domain_analogizer`) — Same differential equation shown in 4 physical domains (mechanical, electrical, acoustic, thermal) with audio synthesis
131. **Convolution Detective** (`convolution_detective`) — Reverse-engineering game: recover unknown impulse response by ear from audio input/output pairs
132. **Bode Plot Constructor & Predictor** (`bode_constructor`) — Interactive s-plane to Bode with asymptotic rule annotations, challenge/prediction/debug modes
133. **Feedback Stability Debugger** (`feedback_stability_debugger`) — Physical system animation synchronized with s-plane pole migration as gain varies

---

## Priority Ranking for IEEE CDC Paper

### Tier 1 — Must Have (directly support paper claims)

| # | Tool | Paper Claim Supported |
|---|------|-----------------------|
| 1 | Root Locus Gain Sweep Explorer | Controller design |
| 2 | Bode Plot Builder | Stability analysis |
| 3 | PID Tuning Lab | PID vs LQR comparison |
| 4 | Nyquist Plot & Stability Criterion | Stability analysis |
| 5 | CT Representation Navigator | Representation conversion |
| 6 | LQR Designer | LQR vs PID comparison |
| 7 | Discretization Method Comparator | CT/DT bridge |
| 8 | Gain & Phase Margin Analyzer | Stability analysis |

### Tier 2 — High Impact (strengthen paper narrative)

| # | Tool | Value |
|---|------|-------|
| 9 | Lead-Lag Compensator Designer | Classical compensator design |
| 10 | Routh-Hurwitz Stability Criterion | Stability fundamentals |
| 11 | Steady-State Error Analyzer | Performance specification |
| 12 | TF to State Space Converter | Representation conversion |
| 13 | Controllability & Observability | Modern control analysis |
| 14 | s-to-z Mapping Visualizer | Discretization insight |
| 15 | Feedback Stability Debugger | Intuition builder |

### Tier 3 — Nice to Have (enriches platform breadth)

Everything else — Fourier tools, modulation tools, convolution visualizers, CD pipeline, etc. These strengthen the "comprehensive textbook" claim but aren't critical for CDC reviewer expectations.
