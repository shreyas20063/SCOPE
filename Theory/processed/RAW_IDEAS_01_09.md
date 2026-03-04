**Lecture 01 — Signals and Systems**
- "Why is a tank leaking like this?": Students struggle to connect water flow rate to system behavior. Let them adjust hole size and inflow rate in real-time, see the tank height respond, and understand why bigger holes = faster drainage.
- "Are sampling and reconstruction opposite?": The jump from continuous to discrete time is abstract. Let students sample a smooth signal at different rates, then try different reconstruction methods (zero-order hold, linear, higher-order) and see the artifacts they create.
- "What does time reversal actually do?": Signal transformations (scaling, shifting, reversing) feel mechanical. Let students drag a waveform around on a time axis, apply f(2t) or f(-t) visually, and see both the formula AND the graph shift/flip simultaneously.

**Lecture 02 — Discrete-Time Systems**
- "Is a delay just shifting or is it something deeper?": Block diagrams show delays as boxes, but students don't feel why the delay operator R is so fundamental. Let them build systems from cascaded delay blocks and watch how the output evolves sample-by-sample, building intuition for R as a primitive operation.
- "Which feedback loops explode and which decay?": The stability of systems with poles at z = 0.5, 1.2, -0.9 feels like magic. Let them drag a pole around the z-plane, see whether responses converge or diverge in real-time, and watch the unit circle as the boundary.
- "How do cascaded systems combine?": Operator algebra (1 - R)^2 = 1 - 2R + R^2 feels unmotivated. Let students connect two difference machines in series, verify the combined output manually, then expand the operator expression and see it match.

**Lecture 03 — Feedback, Poles, and Fundamental Modes**
- "Why does this look like an exponential sum?": The Fibonacci sequence jumping out of h[n] = (4.5)(0.9)^n - (3.5)(0.7)^n from pole factorization seems like black magic. Let students input a signal, see the response build from two decaying exponential modes that interfere, and watch the modes turn on/off.
- "What do complex poles actually mean?": Complex conjugate poles ±jω feel divorced from reality. Let students see oscillating responses arise naturally from pairs of complex poles, and play with pole magnitude (controls decay) and angle (controls oscillation frequency).
- "Can I predict stability just by looking at the block diagram?": Counting cycles and reasoning about growth is hard. Let them click on a cyclic path, see the pole it creates, and instantly know whether it diverges (pole outside unit circle) or converges.

**Lecture 04 — Continuous-Time Systems**
- "How is the A operator like R but different?": The intuition gap between delay (R) and integration (A) is huge. Let them build identical CT and DT systems side-by-side, feed the same input, and watch how integration produces smooth curves while delays produce discrete jumps.
- "Why does the impulse response have exponentials?": The jump from y'(t) = x(t) + py(t) to y(t) = e^(pt)u(t) requires understanding a differential equation solution. Let students adjust p visually, see the pole move in the s-plane, and watch the time-domain response grow or decay accordingly.
- "Does the mass-spring system really oscillate at that frequency?": Complex poles on the imaginary axis are hard to picture. Let them grab the poles and drag them around the s-plane, watch the impulse response change from exponential decay to damped oscillation to pure oscillation, and see the natural frequency emerge.

**Lecture 05 — Z Transform**
- "Why does R → 1/z even matter?": The substitution feels arbitrary. Let students manually convert a system functional H(R) to H(z) using the mapping, then verify by computing the unit-sample response both ways and seeing they agree.
- "What is a region of convergence really?": ROCs (|z| > a, |z| < a, annulus) feel disconnected from time signals. Let them pick a signal, compute its Z transform, shade the ROC, and drag a test point around the z-plane to watch the transform sum converge or diverge.
- "How do poles encode causality?": Right-sided vs. left-sided signals and their ROCs is purely algebraic. Let them select different ROCs for the same rational function and see that poles determine whether the signal extends forward or backward in time.
- "Can I invert a Z transform without a table?": Partial fractions work, but partial-fractions inversion feels rote. Let them design a rational H(z), factor it, write the partial fraction form, and reconstruct h[n] piece-by-piece, seeing each mode contribute its geometric sequence.

**Lecture 06 — Laplace Transform**
- "Why do I need the ROC to be a vertical strip in CT?": Two-sided signals with both left and right sides (like e^(-|t|)) feel weird. Let students input a two-sided signal, compute its Laplace transform, and watch the ROC become a vertical strip bounded by the left and right exponential decay rates.
- "How do poles in the s-plane predict whether a system blows up?": The left half-plane = stable, right half-plane = unstable is stated but not felt. Let them position poles in the s-plane and watch impulse responses either decay or explode in real-time.
- "Why is convolving in time the same as multiplying in frequency?": Convolution is abstract; multiplication is concrete. Let them apply a convolution by hand (messy), then compute it as a product of Laplace transforms and inverse-transform, seeing both routes agree.

**Lecture 07 — Discrete Approximation of Continuous-Time Systems**
- "Why does forward Euler blow up for stiff systems?": The forward Euler approximation DT pole z = 1 - T/τ moves outside the unit circle when T > 2τ, but students don't visualize why. Let them vary T/τ, watch the DT pole trace a path in the z-plane, and see it cross the unit circle at a critical ratio.
- "How do different discretization schemes compare?": Three methods (forward Euler, backward Euler, trapezoidal) are taught as isolated recipes. Let students implement all three on the same CT system, watch their DT poles map to different curves in the z-plane, and see backward Euler's always-stable L-shaped path vs. forward Euler's risky diagonal.
- "What does it mean for a continuous system to stay stable after discretization?": The trapezoidal rule maps the entire left half-plane inside the unit circle. Let them grab a pole in the s-plane, see how it maps to z under different discretization methods, and understand why the trapezoidal rule is "safe" but forward Euler isn't.

**Lecture 08 — Convolution**
- "Why is the convolution formula flipping one signal backwards?": The definition y[n] = ∑x[k]h[n-k] is mechanical. Let students place two signals on an interactive tape, flip one, slide it under the other, multiply pointwise, and sum—turning the formula into a visual/kinesthetic operation.
- "Does convolving a short pulse with itself really give a triangle?": Convolution produces surprising shapes. Let students convolve rectangles, triangles, or other simple signals with themselves and see the output grow in width and change shape in ways that build intuition (e.g., rect ∗ rect = triangle).
- "How is the point-spread function in a microscope a convolution?": The connection between blurring and convolution is profound but abstract. Show before/after Hubble images, reveal they're related by convolution with a point-spread function, and let students reverse it (deconvolve) to deblur interactively.
- "Can a signal be its own inverse under convolution?": Edge case: can x ∗ h = δ? Let students search for such pairs, or start with an h and ask them to design x such that x ∗ h = δ, building intuition for inverse systems.

**Lecture 09 — Frequency Response**
- "Why does a sinusoid in = sinusoid out at the same frequency?": The claim feels magical. Let students input a cosine at variable frequency ω, watch the system's step-by-step output, and see that after transients die out, the steady-state output is indeed a scaled and phase-shifted copy of the input.
- "What do magnitude and phase plots really show?": Bode plots are abstract curves. Let them pick a frequency ω on an interactive plot, see the magnitude and phase values highlighted, and then watch the time-domain input and output signals update to show how much the output is scaled and shifted.
- "How do poles near the jω axis create sharp peaks?": The vector diagram method is geometric but hard to visualize. Let students drag poles around the s-plane near the imaginary axis, watch the distance from jω to each pole shrink, and see the frequency response magnitude spike.
- "Why does a resonant system ring at a specific frequency?": Mass-spring-dashpot systems ring at ω_d, but where does this come from? Let them adjust spring stiffness K and damping B, watch the poles move in the s-plane, and see both the natural frequency and damping ratio change the frequency response peak.
- "Can I sketch a frequency response just from pole positions?": Vector diagrams are the key. Let students place poles and zeros anywhere, then predict the magnitude response by estimating distances from jω to poles/zeros, and verify their prediction by computing the actual response.
