# Raw Idea Seeds: Lectures 10-18 (Confusing Concepts for Interactive Play)

**Lecture 10 — Feedback & Control**
- Drag the gain K on a slider and watch the robot approach the wall in real-time; see it overshoot, oscillate, or nail it perfectly at different K values.
- Toggle sensor delay on/off and watch how the exact same K value suddenly fails when you add a tiny 1-sample delay.

**Lecture 11-2 — CT Frequency Response & Bode Plots**
- Click poles/zeros on the s-plane and see the magnitude and phase plots redraw live; drag a zero toward a pole to watch the notch form.
- Tweak the corner frequency of a single pole and see the asymptotic straight-line approximation snap into place—show where it breaks down vs. the true curve.
- Draw your own Bode plot by hand on a log-frequency axis and compare it to the actual system response in real-time.

**Lecture 12 — CT Feedback & Control**
- Sweep Q from 1 to 100 and watch the peak of a resonant system grow and sharpen; see the 3dB bandwidth collapse.
- Stack multiple poles/zeros and watch their individual Bode contributions add together; remove one and see the overall response change.

**Lecture 13-2 — Fourier Series (CT)**
- Incrementally add harmonics to a square wave and watch it converge to the actual waveform; pause at different N and see the ringing.
- Pick a periodic signal (triangle, sawtooth, square) and animate the Fourier series building up term-by-term; compare convergence speed.
- Change the duty cycle of a square wave and see how the harmonic amplitudes shift.

**Lecture 14-3 — Fourier Series (Speech & Audio)**
- Input a vowel sound or noise and decompose it into its first 5-10 harmonics; mute individual harmonics to hear what each contributes.
- Play a formant sweep (F1 and F2 moving) and watch the spectrum evolve—connect the changing frequency peaks to the changing vowel sound.
- Create your own "vocal tract filter" by drawing a frequency response curve; apply it to a buzzy glottal signal and hear the artificial vowel.

**Lecture 15-2 — Fourier Transform (CT)**
- Stretch a pulse in time and watch its Fourier transform shrink in frequency; see the bandwidth-time trade-off in real-time.
- Delay a pulse by dragging it on the time axis and see the phase spectrum rotate without changing magnitude.
- Compare a square pulse to a Gaussian pulse side-by-side; see why the Gaussian's transform is "nicer" (smoother, no sidelobes).

**Lecture 16-2 — Discrete-Time Frequency Response**
- Place poles and zeros on the z-plane unit circle and watch the frequency response |H(e^jΩ)| update live; drag a pole toward the unit circle and watch the peak sharpen.
- Tune a DT filter and watch real DT sinusoid samples get filtered in real-time on the time-domain plot.
- Show aliasing visually: input a "fast" continuous sinusoid, sample it, and see it alias to a slow sinusoid; adjust the sampling rate.

**Lecture 17 — DT Fourier Series & Representations**
- Build a DT Fourier series by dragging sliders for each of the N harmonic amplitudes; watch the time-domain signal update.
- Take a short periodic sequence (N=4 or 8) and show the finite matrix of complex exponentials; highlight which harmonics matter.
- Compare CT Fourier series to DT Fourier series side-by-side: show how DT has finitely many harmonics (huge relief for students).

**Lecture 18 — DT Fourier Transform & FFT**
- Tweak the length of a rectangular pulse and watch its DT Fourier transform mainlobe widen and sidelobe pattern shift.
- Show a 16-point signal and its DFT with N=16, then N=32 zero-padded; watch how zero-padding makes the frequency bins denser without adding new info.
- Animate the FFT decimation tree (divide and conquer) so students see why it's O(N log N) not O(N²).
