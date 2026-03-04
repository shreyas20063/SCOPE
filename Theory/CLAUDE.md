Claude · MD
# Project: Interactive Simulation Web Textbook for Signals & Systems

## Context
User (Sudeep) is building an **interactive simulation web textbook** based on MIT 6.003 (Signals and Systems) lecture slides. The goal is to go through each lecture (25 total), understand the content, and propose new web-based simulations that complement the existing set.

## Source Material
- **Course**: MIT 6.003F11 — Signals and Systems
- **Lectures**: 25 PDF lecture slide sets located in `/sessions/dreamy-nice-hawking/mnt/Theory/`
- **Naming**: Files are `*_MIT6_003F11_lecXX.pdf` (some have `-2`, `-3` suffixes indicating revised versions)

## Existing Simulations (DO NOT re-propose these)
The user already has 13+ web simulations built with React + FastAPI:
1. Aliasing & Quantization (Nyquist, aliasing, quantization)
2. Amplifier Topologies (simple, feedback, crossover, compensated)
3. Convolution Simulator (step-by-step visualization)
4. CT/DT Poles Conversion (S-plane to Z-plane)
5. DC Motor Control (first/second-order)
6. Feedback System Analysis (Bode plots, pole trajectories)
7. Fourier Phase vs Magnitude (image & audio FFT)
8. Fourier Series (approximations)
9. Furuta Pendulum (3D inverted pendulum, PID)
10. Lens Optics (PSF-based resolution)
11. Modulation Techniques (AM, FM, FDM)
12. RC Lowpass Filter (frequency response)
13. Second-Order System (Q factor, pole-zero)
14. Block Diagram ↔ Transfer Function converter (Simulink-like)

## Tech Stack (Web Only — ignore PyQt5)
- **Backend**: FastAPI, Python 3.11, NumPy, SciPy, WebSocket
- **Frontend**: React 18, Vite, Plotly.js, Three.js
- **Deployment**: Docker, Docker Compose

## Workflow
1. Read one lecture at a time (user says "next" to advance)
2. Summarize the key teachable concepts
3. Cross-reference against existing simulations to avoid duplicates
4. Propose 2-4 new simulation ideas with:
   - Description of what is simulated
   - How the user interacts (sliders, drag-drop, quiz mode, etc.)
   - Which lecture slides it maps to
   - Priority ranking

## Progress Tracker
- [x] Lecture 01 — Intro: Signals & Systems abstraction, CT/DT, sampling/reconstruction, signal operations
  - Proposed: Signal Operations Playground, Sampling & Reconstruction Explorer, Mass-Spring Visualizer, Modular System Chain
- [x] Lecture 02 — Discrete-Time Systems: difference equations, block diagrams, operator notation (R), feedback, cyclic paths, FIR/IIR, geometric modes, convergence/divergence
  - Proposed: DT Step-by-Step Solver, Operator Algebra Visualizer, Feedback & Convergence Explorer, Cyclic Path Detector
- [x] Lecture 03 — Feedback, Poles, and Fundamental Modes: poles as geometric sequence bases, 4 pole regimes (real line), second-order factoring, cascade vs parallel forms, partial fractions, fundamental modes as weighted sums
  - Proposed: Pole Behavior Explorer, Cascade ↔ Parallel Decomposition Workbench, Polynomial Multiplication Visualizer, Fundamental Modes Superposition Demo
- [x] Lecture 04 — Continuous-Time Systems: 𝒜 operator (integration), CT block diagrams, δ(t) impulse as limit, unit step u(t), CT feedback → eᵖᵗ via operator series, convergence (left half-plane vs unit circle), mass-spring complex poles → sinusoidal modes
  - Proposed: CT Impulse Response Builder, DT ↔ CT Side-by-Side Comparator, Unit Impulse δ(t) Construction Lab, Complex Poles & Sinusoidal Modes Visualizer
- [x] Lecture 05 — Z Transform: DT concept map (5 representations), Z transform definition H(z)=Σh[n]z⁻ⁿ, bilateral transform, Z transform pairs, Region of Convergence (ROC), ROC determines causality (same H(z) → different signals), rational polynomials/poles/zeros, Z transform properties (linearity, delay, multiply-by-n, convolution), inverse Z transform via partial fractions, solving difference equations via Z transform
  - Proposed: Z Transform & ROC Explorer, Inverse Z Transform Step-by-Step Solver, Z Transform Properties Lab, DT System Representation Navigator
- [x] Lecture 06 — Laplace Transform: CT concept map (5 representations), Laplace definition X(s)=∫x(t)e⁻ˢᵗdt, bilateral vs unilateral, s-plane ROC (vertical strips), ROC determines causality (right-sided/left-sided/two-sided), Laplace of derivative (sX(s)), solving differential equations via Laplace, Laplace properties (linearity, delay, multiply-by-t, frequency shift, differentiate, integrate, convolve), initial & final value theorems
  - Proposed: Laplace Transform & s-Plane ROC Explorer, Differential Equation Solver via Laplace, Initial & Final Value Theorem Visualizer, Laplace Properties Lab
- [x] Lecture 07 — Discrete Approximation of CT Systems: leaky tank example (τṙ=x−y, H(s)=1/(1+τs)), step response derivation, Forward Euler (ẏ≈(y[n+1]−y[n])/T → z=1+sT, pole at 1−T/τ, conditionally stable T/τ<2), Backward Euler (ẏ≈(y[n]−y[n−1])/T → z=1/(1−sT), unconditionally stable), Trapezoidal Rule / Bilinear Transform (centered differences → z=(2+sT)/(2−sT), jω axis→unit circle, best preservation), s-to-z mapping comparison for all three methods, mass-spring system discretization example
  - Proposed: Discretization Method Comparator, s-to-z Mapping Visualizer, Numerical Integration Explorer, Leaky Tank Simulator
- [x] Lecture 08 — Convolution: 6th system representation (impulse response), responses to arbitrary signals via block diagram step-by-step, superposition (linearity + time-invariance), DT convolution y[n]=Σx[k]h[n−k] (flip-shift-multiply-sum), notation (signals not samples), CT convolution y(t)=∫x(τ)h(t−τ)dτ (pulse approximation → integral limit), worked examples (geometric series, e⁻ᵗu(t)*e⁻ᵗu(t)=te⁻ᵗu(t)), applications: microscope PSF (3D impulse response), Hubble cascade blur h_t=h_a*h_d, COSTAR corrective optics/deconvolution
  - Proposed: LTI System Tester, Superposition Decomposition Visualizer, CT Convolution Integral Visualizer, Cascade Convolution & Deconvolution Explorer
- [x] Lecture 09 — Frequency Response: frequency response definition (|H(jω)|, ∠H(jω)), eigenfunctions & eigenvalues of LTI systems (complex exponentials eˢᵗ → eigenvalue H(s)), conjugate symmetry H(−jω)=H(jω)*, rational system functions N(s)/D(s), vector diagram method (graphical pole-zero → frequency response construction), magnitude = product of vector lengths, phase = sum of angles, mass-spring-dashpot resonance (ω₀ vs ω_d vs ω_peak distinctions), peak frequency ω²=ω₀²−2σ², phase = −π/2 at ω=ω₀
  - Proposed: Vector Diagram Frequency Response Builder, Eigenfunction Tester Lab, Resonance Anatomy Explorer, Audio Frequency Response Playground
- [ ] Lecture 10
- [ ] Lecture 11
- [ ] Lecture 12
- [ ] Lecture 13
- [ ] Lecture 14
- [ ] Lecture 15
- [ ] Lecture 16
- [ ] Lecture 17
- [ ] Lecture 18
- [ ] Lecture 19
- [ ] Lecture 20
- [ ] Lecture 21
- [ ] Lecture 22
- [ ] Lecture 23
- [ ] Lecture 24
- [ ] Lecture 25

## Key Preferences
- **Web simulations only** (no PyQt5)
- Focus on interactive, visual, pedagogically valuable simulations
- User is a coder — technical detail is welcome
- Propose ideas first, build when asked