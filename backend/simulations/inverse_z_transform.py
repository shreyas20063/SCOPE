"""
Inverse Z Transform Step-by-Step Solver

Given a rational H(z) = N(z)/D(z) and an ROC specification, walks through
the full inverse Z transform pipeline:
  (a) factor the denominator to find poles
  (b) perform partial fraction decomposition (showing the algebra)
  (c) match each term to a standard Z transform pair based on the ROC
  (d) assemble the final time-domain signal h[n]

Supports three solution methods:
  A) Partial fractions (standard)
  B) Long division
  C) Power series expansion

Includes quiz mode where user guesses residues before reveal.

Based on MIT 6.003 Lecture 5, Slides 34–50.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.signal import residuez

from .base_simulator import BaseSimulator


class InverseZTransformSimulator(BaseSimulator):
    """Simulator for step-by-step inverse Z transform computation."""

    MAX_STEP = 4
    CLAMP_VALUE = 200.0

    # ── Presets ───────────────────────────────────────────────────

    PRESETS: Dict[str, Dict[str, Any]] = {
        "example_1": {
            "label": "Slide 35: H(z) = z / ((z−0.5)(z−0.8))",
            "num_z": [1, 0],           # z
            "den_z": [1, -1.3, 0.4],   # z² − 1.3z + 0.4 = (z−0.5)(z−0.8)
            "description": "Two real distinct poles at 0.5 and 0.8",
        },
        "example_2": {
            "label": "Slide 38: H(z) = 1 / ((1−0.5z⁻¹)(1+0.3z⁻¹))",
            "num_z": [1],              # 1  (in z⁻¹: just [1])
            "den_z": [1, -0.2, -0.15], # z² − 0.2z − 0.15
            "description": "Standard partial fraction example",
        },
        "example_3": {
            "label": "Repeated pole: H(z) = z² / (z−0.5)²",
            "num_z": [1, 0, 0],        # z²
            "den_z": [1, -1.0, 0.25],  # (z−0.5)²
            "description": "Repeated real pole at z = 0.5",
        },
        "example_4": {
            "label": "Complex poles: H(z) = 1 / (z²−z+0.5)",
            "num_z": [1],
            "den_z": [1, -1.0, 0.5],
            "description": "Complex conjugate poles at 0.5 ± 0.5j",
        },
        "example_5": {
            "label": "Mixed: H(z) = z / ((z−2)(z−0.5))",
            "num_z": [1, 0],           # z
            "den_z": [1, -2.5, 1.0],   # z² − 2.5z + 1
            "description": "Pole at z=2 (outside unit circle) — requires careful ROC",
        },
    }

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "example_1", "label": "Slide 35: z/((z−0.5)(z−0.8))"},
                {"value": "example_2", "label": "Slide 38: Standard PFE"},
                {"value": "example_3", "label": "Repeated Pole"},
                {"value": "example_4", "label": "Complex Poles"},
                {"value": "example_5", "label": "Mixed Causal/Anticausal"},
                {"value": "custom", "label": "Custom Coefficients"},
            ],
            "default": "example_1",
        },
        "num_coeffs": {
            "type": "expression",
            "default": "1, 0",
        },
        "den_coeffs": {
            "type": "expression",
            "default": "1, -1.3, 0.4",
        },
        "roc_type": {
            "type": "select",
            "options": [
                {"value": "causal", "label": "Causal (|z| > max|pole|)"},
                {"value": "anticausal", "label": "Anti-causal (|z| < min|pole|)"},
                {"value": "custom", "label": "Custom (per-pole in viewer)"},
            ],
            "default": "causal",
        },
        "active_method": {
            "type": "select",
            "options": [
                {"value": "partial_fractions", "label": "A: Partial Fractions"},
                {"value": "long_division", "label": "B: Long Division"},
                {"value": "power_series", "label": "C: Power Series"},
            ],
            "default": "partial_fractions",
        },
        "mode": {
            "type": "select",
            "options": [
                {"value": "solve", "label": "Solve"},
                {"value": "quiz", "label": "Quiz"},
            ],
            "default": "solve",
        },
        "num_samples": {
            "type": "slider",
            "min": 10,
            "max": 60,
            "step": 1,
            "default": 30,
        },
    }

    DEFAULT_PARAMS = {
        "preset": "example_1",
        "num_coeffs": "1, 0",
        "den_coeffs": "1, -1.3, 0.4",
        "roc_type": "causal",
        "active_method": "partial_fractions",
        "mode": "solve",
        "num_samples": 30,
    }

    # ── Init ──────────────────────────────────────────────────────

    def __init__(self, simulation_id: str) -> None:
        super().__init__(simulation_id)

        self._current_step: int = 0

        # Polynomial coefficients (descending powers of z)
        self._num_z: List[float] = []
        self._den_z: List[float] = []

        # Computed quantities
        self._poles: np.ndarray = np.array([])
        self._zeros: np.ndarray = np.array([])
        self._residues: np.ndarray = np.array([])
        self._direct_terms: np.ndarray = np.array([])
        self._pole_multiplicity: Dict[int, int] = {}

        # ROC per-pole assignment
        self._roc_regions: List[Dict[str, Any]] = []

        # Solution steps
        self._solution_steps: List[Dict[str, Any]] = []
        self._method_b_steps: List[Dict[str, Any]] = []
        self._method_c_terms: List[float] = []

        # Time-domain result
        self._h_n: Optional[np.ndarray] = None
        self._n: Optional[np.ndarray] = None
        self._is_stable: bool = True

        # Quiz state
        self._quiz_active: bool = False
        self._quiz_checked: bool = False
        self._quiz_scores: List[Dict[str, Any]] = []

    # ── Lifecycle ─────────────────────────────────────────────────

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._current_step = 0
        self._quiz_active = False
        self._quiz_checked = False
        self._quiz_scores = []
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # Reset steps when system or view mode changes
            if name in ("preset", "num_coeffs", "den_coeffs", "roc_type", "mode", "active_method"):
                self._current_step = 0
                self._quiz_active = False
                self._quiz_checked = False
                self._quiz_scores = []
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        self._current_step = 0
        self._quiz_active = False
        self._quiz_checked = False
        self._quiz_scores = []
        return super().reset()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "next_step":
            self._current_step = min(self._current_step + 1, self.MAX_STEP)
        elif action == "prev_step":
            self._current_step = max(self._current_step - 1, 0)
        elif action == "show_all":
            self._current_step = self.MAX_STEP
        elif action == "reset_steps":
            self._current_step = 0
            self._quiz_active = False
            self._quiz_checked = False
            self._quiz_scores = []
        elif action == "set_roc_region":
            idx = int(params.get("pole_index", 0))
            causal = bool(params.get("causal", True))
            if 0 <= idx < len(self._roc_regions):
                self._roc_regions[idx]["causal"] = causal
            self._assemble_time_domain()
            self._build_solution_steps()
        elif action == "check_quiz":
            self._check_quiz(params.get("answers", {}))
        elif action == "new_quiz":
            self._start_quiz()
        return self.get_state()

    # ── Coefficient parsing ───────────────────────────────────────

    def _parse_coeffs(self, expr: str) -> List[float]:
        """Parse comma-separated coefficient string into list of floats."""
        try:
            parts = [s.strip() for s in expr.split(",") if s.strip()]
            return [float(p) for p in parts]
        except (ValueError, TypeError):
            return [1.0]

    def _load_coefficients(self) -> None:
        """Load numerator/denominator from preset or custom input."""
        preset = self.parameters.get("preset", "example_1")

        if preset != "custom" and preset in self.PRESETS:
            p = self.PRESETS[preset]
            self._num_z = list(p["num_z"])
            self._den_z = list(p["den_z"])
        else:
            self._num_z = self._parse_coeffs(str(self.parameters.get("num_coeffs", "1")))
            self._den_z = self._parse_coeffs(str(self.parameters.get("den_coeffs", "1, -0.5")))

        # Ensure denominator is non-trivial
        if not self._den_z or all(abs(c) < 1e-15 for c in self._den_z):
            self._den_z = [1.0]

    @staticmethod
    def _poly_z_to_zinv(coeffs_z: List[float]) -> np.ndarray:
        """Convert polynomial in descending z to z⁻¹ form for residuez.

        coeffs_z: [a0, a1, ..., aN] representing a0*z^N + a1*z^(N-1) + ... + aN
        Returns: [a0, a1, ..., aN] as coefficients of [1, z^-1, z^-2, ...] * z^N
        For residuez, we need coefficients of z⁻¹: [b0, b1, ...] = N(z)/z^M / D(z)/z^N
        """
        return np.array(coeffs_z, dtype=float)

    # ── Core computation ──────────────────────────────────────────

    def _compute(self) -> None:
        """Full computation pipeline."""
        self._load_coefficients()

        b_z = np.array(self._num_z, dtype=float)
        a_z = np.array(self._den_z, dtype=float)

        # Find zeros from numerator polynomial
        if len(b_z) > 1:
            self._zeros = np.roots(b_z)
        else:
            self._zeros = np.array([])

        # Partial fraction decomposition using residuez
        # residuez expects coefficients in z⁻¹ form: H(z) = B(z⁻¹)/A(z⁻¹)
        b_zinv, a_zinv = self._convert_to_zinv_form(b_z, a_z)

        try:
            self._residues, poles_pfe, self._direct_terms = residuez(b_zinv, a_zinv)
            # Use poles from residuez — guaranteed to match residue ordering
            self._poles = poles_pfe
        except Exception:
            # Fallback: compute poles from roots, no residues
            self._poles = np.roots(a_z) if len(a_z) > 1 else np.array([])
            self._residues = np.array([])
            self._direct_terms = np.array([])

        # Initialize ROC regions
        self._init_roc_regions()

        # Stability check (causal assumption)
        self._is_stable = all(abs(p) < 1.0 for p in self._poles) if len(self._poles) > 0 else True

        # Assemble time-domain signal
        self._assemble_time_domain()

        # Compute alternative methods
        self._compute_long_division(b_zinv, a_zinv)
        self._compute_power_series(b_zinv, a_zinv)

        # Build solution steps
        self._build_solution_steps()

    def _convert_to_zinv_form(
        self, b_z: np.ndarray, a_z: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert H(z) = B(z)/A(z) to H(z) = B'(z⁻¹)/A'(z⁻¹) for residuez.

        B(z) = b0*z^M + b1*z^(M-1) + ... + bM  (descending z)
        A(z) = a0*z^N + a1*z^(N-1) + ... + aN  (descending z)

        Dividing both by z^N:
          B(z)/z^N = b0*z^(M-N) + ... → z⁻¹ coeffs need (N-M) leading zeros
          A(z)/z^N = a0 + a1*z⁻¹ + ... + aN*z⁻N (already in z⁻¹ form)

        residuez expects coefficients of [z^0, z^(-1), z^(-2), ...].
        """
        M = len(b_z) - 1  # degree of numerator in z
        N = len(a_z) - 1  # degree of denominator in z

        # Normalize by leading coefficient of denominator
        a0 = a_z[0]
        if abs(a0) > 1e-15:
            b_z = b_z / a0
            a_z = a_z / a0

        # When M < N, the z⁻¹ form numerator has (N-M) leading zeros
        # Example: B(z) = z → [1,0] in z-desc, degree M=1
        #   For N=2: B(z)/z² = z⁻¹ → z⁻¹ coeffs = [0, 1]
        if M < N:
            b_zinv = np.concatenate([np.zeros(N - M), b_z])
        else:
            b_zinv = b_z

        return b_zinv.copy(), a_z.copy()

    def _init_roc_regions(self) -> None:
        """Initialize ROC regions based on roc_type parameter."""
        roc_type = self.parameters.get("roc_type", "causal")

        self._roc_regions = []
        for i, p in enumerate(self._poles):
            mag = float(abs(p))
            if roc_type == "causal":
                causal = True
            elif roc_type == "anticausal":
                causal = False
            else:
                # Custom: default to causal for poles inside unit circle,
                # anticausal for poles outside
                causal = mag < 1.0
            self._roc_regions.append({
                "pole_index": i,
                "causal": causal,
                "pole_magnitude": mag,
                "pole_real": float(p.real),
                "pole_imag": float(p.imag),
            })

    # ── Time-domain assembly ──────────────────────────────────────

    def _assemble_time_domain(self) -> None:
        """Build h[n] from partial fractions and ROC assignments."""
        N = int(self.parameters.get("num_samples", 30))

        # Include negative indices for anticausal parts
        has_anticausal = any(not r["causal"] for r in self._roc_regions)
        n_start = -(N // 3) if has_anticausal else 0
        n = np.arange(n_start, N)
        self._n = n

        h = np.zeros(len(n), dtype=complex)

        if len(self._residues) == 0:
            self._h_n = np.real(h)
            return

        # Add partial fraction terms
        for i, (r, p) in enumerate(zip(self._residues, self._poles)):
            if i < len(self._roc_regions):
                is_causal = self._roc_regions[i]["causal"]
            else:
                is_causal = True

            if is_causal:
                # Causal: r * p^n * u[n]
                mask = n >= 0
                n_pos = n[mask].astype(float)
                h[mask] += r * (p ** n_pos)
            else:
                # Anti-causal: -r * p^n * u[-n-1]
                mask = n < 0
                n_neg = n[mask].astype(float)
                h[mask] -= r * (p ** n_neg)

        # Add direct (FIR) terms: d[0]*delta[n] + d[1]*delta[n-1] + ...
        for k, d in enumerate(self._direct_terms):
            idx = np.where(n == k)[0]
            if len(idx) > 0:
                h[idx[0]] += d

        self._h_n = np.clip(np.real(h), -self.CLAMP_VALUE, self.CLAMP_VALUE)

    # ── Long division (Method B) ──────────────────────────────────

    def _compute_long_division(
        self, b_zinv: np.ndarray, a_zinv: np.ndarray, num_terms: int = 12
    ) -> None:
        """Polynomial long division of B(z⁻¹)/A(z⁻¹) for first num_terms."""
        self._method_b_steps = []

        if len(a_zinv) == 0 or abs(a_zinv[0]) < 1e-15:
            return

        remainder = list(b_zinv)
        a = list(a_zinv)

        for i in range(num_terms):
            if not remainder or all(abs(r) < 1e-15 for r in remainder):
                break

            q = remainder[0] / a[0]

            # Subtract q * a from remainder
            subtracted = [q * a_k for a_k in a]
            new_rem = []
            for j in range(max(len(remainder), len(subtracted))):
                r_val = remainder[j] if j < len(remainder) else 0.0
                s_val = subtracted[j] if j < len(subtracted) else 0.0
                new_rem.append(r_val - s_val)

            self._method_b_steps.append({
                "term_index": i,
                "coefficient": float(np.real(q)),
                "equation": f"h[{i}] = {float(np.real(q)):.6g}",
                "remainder_before": [float(np.real(x)) for x in remainder[:4]],
                "remainder_after": [float(np.real(x)) for x in new_rem[1:4]],
            })

            remainder = new_rem[1:]  # shift by one power of z⁻¹

    # ── Power series (Method C) ───────────────────────────────────

    def _compute_power_series(
        self, b_zinv: np.ndarray, a_zinv: np.ndarray, num_terms: int = 15
    ) -> None:
        """Compute h[n] recursively from difference equation."""
        self._method_c_terms = []

        if len(a_zinv) == 0 or abs(a_zinv[0]) < 1e-15:
            return

        # Normalize: a[0] = 1
        b = b_zinv / a_zinv[0]
        a = a_zinv / a_zinv[0]

        h = []
        for n_val in range(num_terms):
            val = float(b[n_val]) if n_val < len(b) else 0.0
            for k in range(1, len(a)):
                if n_val - k >= 0 and n_val - k < len(h):
                    val -= float(a[k]) * h[n_val - k]
            h.append(val)

        self._method_c_terms = h

    # ── Solution step builder ─────────────────────────────────────

    def _build_solution_steps(self) -> None:
        """Build the step-by-step solution explanation."""
        self._solution_steps = [
            self._step_0_original(),
            self._step_1_factor(),
            self._step_2_partial_fractions(),
            self._step_3_zt_pairs(),
            self._step_4_assemble(),
        ]

    def _step_0_original(self) -> Dict[str, Any]:
        num_str = self._format_poly(self._num_z, "z")
        den_str = self._format_poly(self._den_z, "z")
        return {
            "step": 0,
            "title": "Original Transfer Function",
            "equation": f"H(z) = ({num_str}) / ({den_str})",
            "description": self._get_preset_description(),
            "details": {},
        }

    def _step_1_factor(self) -> Dict[str, Any]:
        if len(self._poles) == 0:
            return {
                "step": 1,
                "title": "Factor Denominator",
                "equation": "D(z) has no poles (constant denominator)",
                "description": "No factoring needed.",
                "details": {},
            }

        # Build factored form string
        factors = []
        for p in self._poles:
            factors.append(f"(z − {self._fmt_complex(p)})")
        leading = self._den_z[0] if abs(self._den_z[0] - 1.0) > 1e-10 else ""
        leading_str = f"{leading:.4g}·" if leading else ""
        factored = f"{leading_str}{''.join(factors)}"

        # Discriminant info for quadratic
        disc_info = ""
        if len(self._den_z) == 3:
            a, b, c = self._den_z[0], self._den_z[1], self._den_z[2]
            disc = b * b - 4 * a * c
            disc_info = f"Discriminant Δ = b²−4ac = ({b:.4g})²−4({a:.4g})({c:.4g}) = {disc:.4g}"
            if disc < 0:
                disc_info += " < 0 → complex conjugate poles"
            elif abs(disc) < 1e-10:
                disc_info += " = 0 → repeated pole"
            else:
                disc_info += " > 0 → real distinct poles"

        pole_list = ", ".join(
            f"p{i+1} = {self._fmt_complex(p)} (|p| = {abs(p):.4f})"
            for i, p in enumerate(self._poles)
        )

        return {
            "step": 1,
            "title": "Factor Denominator & Find Poles",
            "equation": f"D(z) = {factored}",
            "description": f"Poles: {pole_list}",
            "details": {
                "discriminant": disc_info,
                "factored_form": factored,
            },
        }

    def _step_2_partial_fractions(self) -> Dict[str, Any]:
        if len(self._residues) == 0:
            return {
                "step": 2,
                "title": "Partial Fraction Decomposition",
                "equation": "No partial fractions (trivial case)",
                "description": "",
                "details": {},
            }

        # Build PFE string
        terms = []
        algebra_steps = []
        for i, (r, p) in enumerate(zip(self._residues, self._poles)):
            r_str = self._fmt_complex(r)
            p_str = self._fmt_complex(p)
            terms.append(f"{r_str} / (1 − {p_str}·z⁻¹)")

            # Show algebra for computing this residue
            algebra_steps.append({
                "index": i,
                "residue": r_str,
                "pole": p_str,
                "explanation": f"R{i+1}: Multiply H(z)·(1−{p_str}·z⁻¹), evaluate at z = {p_str}  →  R{i+1} = {r_str}",
            })

        # Direct terms
        direct_str = ""
        if len(self._direct_terms) > 0 and any(abs(d) > 1e-10 for d in self._direct_terms):
            direct_parts = []
            for k, d in enumerate(self._direct_terms):
                if abs(d) > 1e-10:
                    direct_parts.append(f"{float(np.real(d)):.4g}·z⁻{k}" if k > 0 else f"{float(np.real(d)):.4g}")
            direct_str = " + " + " + ".join(direct_parts)

        pfe_str = " + ".join(terms) + direct_str

        return {
            "step": 2,
            "title": "Partial Fraction Decomposition",
            "equation": f"H(z) = {pfe_str}",
            "description": f"Decomposed into {len(self._residues)} partial fraction term(s).",
            "details": {
                "algebra_steps": algebra_steps,
                "has_direct_terms": len(self._direct_terms) > 0 and any(abs(d) > 1e-10 for d in self._direct_terms),
            },
        }

    def _step_3_zt_pairs(self) -> Dict[str, Any]:
        if len(self._residues) == 0:
            return {
                "step": 3,
                "title": "Match Z-Transform Pairs",
                "equation": "—",
                "description": "",
                "details": {"pairs": []},
            }

        pairs = []
        for i, (r, p) in enumerate(zip(self._residues, self._poles)):
            is_causal = self._roc_regions[i]["causal"] if i < len(self._roc_regions) else True
            r_str = self._fmt_complex(r)
            p_str = self._fmt_complex(p)
            mag = abs(p)

            if is_causal:
                zt_pair = f"R/(1−p·z⁻¹) ↔ R·pⁿ·u[n]  (ROC: |z| > {mag:.4f})"
                time_term = f"{r_str}·({p_str})ⁿ·u[n]"
            else:
                zt_pair = f"R/(1−p·z⁻¹) ↔ −R·pⁿ·u[−n−1]  (ROC: |z| < {mag:.4f})"
                time_term = f"−{r_str}·({p_str})ⁿ·u[−n−1]"

            pairs.append({
                "index": i,
                "residue": r_str,
                "pole": p_str,
                "causal": is_causal,
                "zt_pair": zt_pair,
                "time_term": time_term,
                "pole_magnitude": float(mag),
            })

        # ROC description
        causal_mags = [abs(self._poles[r["pole_index"]]) for r in self._roc_regions if r["causal"]]
        anticausal_mags = [abs(self._poles[r["pole_index"]]) for r in self._roc_regions if not r["causal"]]

        roc_desc = "ROC: "
        if anticausal_mags and causal_mags:
            roc_desc += f"{max(causal_mags):.4f} < |z| < {min(anticausal_mags):.4f}" if max(causal_mags) < min(anticausal_mags) else "Multiple regions"
        elif causal_mags:
            roc_desc += f"|z| > {max(causal_mags):.4f}"
        elif anticausal_mags:
            roc_desc += f"|z| < {min(anticausal_mags):.4f}"
        else:
            roc_desc += "entire z-plane"

        return {
            "step": 3,
            "title": "Match Z-Transform Pairs (ROC)",
            "equation": roc_desc,
            "description": "Each partial fraction term maps to a standard Z-transform pair.",
            "details": {"pairs": pairs},
        }

    def _step_4_assemble(self) -> Dict[str, Any]:
        if len(self._residues) == 0:
            return {
                "step": 4,
                "title": "Assemble h[n]",
                "equation": "h[n] = 0",
                "description": "",
                "details": {},
            }

        terms = []
        for i, (r, p) in enumerate(zip(self._residues, self._poles)):
            is_causal = self._roc_regions[i]["causal"] if i < len(self._roc_regions) else True
            r_str = self._fmt_complex(r)
            p_str = self._fmt_complex(p)

            if is_causal:
                terms.append(f"{r_str}·({p_str})ⁿ·u[n]")
            else:
                terms.append(f"(−{r_str})·({p_str})ⁿ·u[−n−1]")

        # Check stability for causal system
        stability = ""
        if all(r.get("causal", True) for r in self._roc_regions):
            if self._is_stable:
                stability = "System is STABLE (all poles inside unit circle)."
            else:
                stability = "System is UNSTABLE (pole(s) outside unit circle)."

        return {
            "step": 4,
            "title": "Assemble Time-Domain Signal",
            "equation": f"h[n] = {' + '.join(terms)}",
            "description": stability,
            "details": {
                "is_stable": self._is_stable,
                "expression_terms": terms,
            },
        }

    # ── Quiz mode ─────────────────────────────────────────────────

    def _start_quiz(self) -> None:
        self._quiz_active = True
        self._quiz_checked = False
        self._quiz_scores = []
        self._current_step = 1  # Show poles but not residues yet

    def _check_quiz(self, answers: Dict) -> None:
        self._quiz_checked = True
        self._quiz_scores = []

        for idx_str, ans in answers.items():
            idx = int(idx_str)
            try:
                user_real = float(ans.get("real", 0))
                user_imag = float(ans.get("imag", 0))
            except (TypeError, ValueError):
                user_real, user_imag = 0.0, 0.0

            user_val = complex(user_real, user_imag)

            if idx < len(self._residues):
                actual = self._residues[idx]
                tolerance = max(0.1 * abs(actual), 0.05)
                is_correct = abs(user_val - actual) < tolerance
            else:
                actual = complex(0, 0)
                is_correct = False

            self._quiz_scores.append({
                "index": idx,
                "correct": bool(is_correct),
                "user_real": user_real,
                "user_imag": user_imag,
                "actual_real": float(actual.real),
                "actual_imag": float(actual.imag),
            })

    # ── Plot generation ───────────────────────────────────────────

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._n is None:
            self._compute()

        plots = [self._make_pole_zero_plot()]

        # Show impulse response from step 3 onward
        if self._current_step >= 3:
            plots.append(self._make_impulse_response_plot())

        # Show magnitude response at final step
        if self._current_step >= 4:
            plots.append(self._make_magnitude_response_plot())

        return plots

    def _make_pole_zero_plot(self) -> Dict[str, Any]:
        traces: List[Dict[str, Any]] = []

        # Unit circle
        theta = np.linspace(0, 2 * np.pi, 200)
        traces.append({
            "x": np.cos(theta).tolist(),
            "y": np.sin(theta).tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1.5, "dash": "dash"},
            "name": "Unit Circle",
            "hoverinfo": "skip",
        })

        # Poles (× markers)
        if len(self._poles) > 0:
            traces.append({
                "x": [float(p.real) for p in self._poles],
                "y": [float(p.imag) for p in self._poles],
                "type": "scatter",
                "mode": "markers+text",
                "marker": {"symbol": "x", "size": 14, "color": "#ef4444", "line": {"width": 3, "color": "#ef4444"}},
                "text": [f"p{i+1}" for i in range(len(self._poles))],
                "textposition": "top right",
                "textfont": {"size": 10, "color": "#ef4444"},
                "name": "Poles",
                "hovertemplate": "Pole: %{x:.4f} + %{y:.4f}j<br>|p| = %{customdata:.4f}<extra></extra>",
                "customdata": [float(abs(p)) for p in self._poles],
            })

        # Zeros (○ markers)
        if len(self._zeros) > 0:
            traces.append({
                "x": [float(z.real) for z in self._zeros],
                "y": [float(z.imag) for z in self._zeros],
                "type": "scatter",
                "mode": "markers",
                "marker": {"symbol": "circle-open", "size": 14, "color": "#3b82f6", "line": {"width": 3}},
                "name": "Zeros",
                "hovertemplate": "Zero: %{x:.4f} + %{y:.4f}j<extra></extra>",
            })

        # ROC shading via layout shapes
        shapes = self._build_roc_shapes()

        # Axis range
        all_pts = list(self._poles) + list(self._zeros)
        max_r = max((abs(p) for p in all_pts), default=1.0) * 1.4
        max_r = max(max_r, 1.5)

        layout = self._base_layout("Re{z}", "Im{z}")
        layout["title"] = {"text": "Pole-Zero Map & ROC", "font": {"size": 14, "color": "#f1f5f9"}}
        layout["xaxis"]["range"] = [-max_r, max_r]
        layout["yaxis"]["range"] = [-max_r, max_r]
        layout["yaxis"]["scaleanchor"] = "x"
        layout["yaxis"]["scaleratio"] = 1
        layout["shapes"] = shapes
        layout["uirevision"] = self._revision_key("pole_zero_map")

        return {"id": "pole_zero_map", "title": "Pole-Zero Map & ROC", "data": traces, "layout": layout}

    def _build_roc_shapes(self) -> List[Dict[str, Any]]:
        """Build Plotly shapes for ROC shading."""
        shapes = []

        if len(self._poles) == 0:
            return shapes

        # Sort unique pole magnitudes
        mags = sorted(set(round(abs(p), 10) for p in self._poles))

        # Determine ROC based on current settings
        roc_type = self.parameters.get("roc_type", "causal")

        if roc_type == "causal":
            # ROC: |z| > max|pole|  → shade outside largest pole circle
            r_inner = max(mags)
            shapes.append(self._annular_shape(r_inner, max(mags) * 2.5, "rgba(16,185,129,0.08)"))
        elif roc_type == "anticausal":
            # ROC: |z| < min|pole|  → shade inside smallest pole circle
            r_outer = min(mags)
            shapes.append(self._annular_shape(0, r_outer, "rgba(59,130,246,0.08)"))
        else:
            # Custom: shade based on per-pole assignments
            # For each annular region between consecutive pole magnitudes,
            # determine if it's in the ROC
            boundaries = [0] + mags + [max(mags) * 2.5]
            for j in range(len(boundaries) - 1):
                r_in = boundaries[j]
                r_out = boundaries[j + 1]
                # A region is in the ROC if it's outside all causal poles
                # and inside all anticausal poles
                in_roc = True
                for reg in self._roc_regions:
                    pm = reg["pole_magnitude"]
                    if reg["causal"] and r_in < pm:
                        in_roc = False
                    if not reg["causal"] and r_out > pm:
                        in_roc = False
                if in_roc:
                    shapes.append(self._annular_shape(r_in, r_out, "rgba(16,185,129,0.08)"))

        # Draw circles at each pole magnitude
        for m in mags:
            theta = np.linspace(0, 2 * np.pi, 100)
            shapes.append({
                "type": "path",
                "path": self._circle_path(m),
                "line": {"color": "rgba(239,68,68,0.3)", "width": 1, "dash": "dot"},
            })

        return shapes

    @staticmethod
    def _circle_path(r: float, n_pts: int = 60) -> str:
        """Generate SVG path string for a circle of radius r."""
        theta = np.linspace(0, 2 * np.pi, n_pts + 1)
        pts = [f"{'M' if i == 0 else 'L'} {r * np.cos(t):.4f},{r * np.sin(t):.4f}"
               for i, t in enumerate(theta)]
        return " ".join(pts) + " Z"

    @staticmethod
    def _annular_shape(r_inner: float, r_outer: float, fillcolor: str) -> Dict[str, Any]:
        """Build a filled circle shape (Plotly shape) for ROC region."""
        return {
            "type": "circle",
            "x0": -r_outer, "y0": -r_outer,
            "x1": r_outer, "y1": r_outer,
            "fillcolor": fillcolor,
            "line": {"width": 0},
            "layer": "below",
        }

    def _make_impulse_response_plot(self) -> Dict[str, Any]:
        n = self._n
        h = self._h_n
        N = len(n)
        traces: List[Dict[str, Any]] = []

        if n is None or h is None:
            return {"id": "impulse_response", "title": "h[n]", "data": [], "layout": self._base_layout("n", "h[n]")}

        # Stem lines
        for i in range(N):
            traces.append({
                "x": [int(n[i]), int(n[i])],
                "y": [0, float(h[i])],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#3b82f6", "width": 2},
                "showlegend": False,
                "hoverinfo": "skip",
            })

        # Markers
        traces.append({
            "x": n.tolist(),
            "y": h.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {"color": "#3b82f6", "size": 8, "line": {"color": "rgba(0,0,0,0.3)", "width": 1}},
            "name": "h[n]",
            "hovertemplate": "n=%{x}<br>h[n]=%{y:.4g}<extra></extra>",
        })

        # Power series overlay if method C active
        if self.parameters.get("active_method") == "power_series" and self._method_c_terms:
            n_ps = list(range(len(self._method_c_terms)))
            traces.append({
                "x": n_ps,
                "y": self._method_c_terms,
                "type": "scatter",
                "mode": "markers",
                "marker": {"color": "#f59e0b", "size": 6, "symbol": "diamond"},
                "name": "Power Series",
                "hovertemplate": "n=%{x}<br>h[n]=%{y:.4g}<extra></extra>",
            })

        layout = self._base_layout("n", "h[n]")
        layout["title"] = {"text": "Impulse Response h[n]", "font": {"size": 14, "color": "#f1f5f9"}}
        layout["yaxis"]["autorange"] = True
        layout["xaxis"]["range"] = [int(n[0]) - 0.5, int(n[-1]) + 0.5]
        layout["xaxis"]["dtick"] = max(1, N // 20)
        layout["uirevision"] = self._revision_key("impulse_response")

        # Zero line
        layout["shapes"] = [{
            "type": "line",
            "x0": int(n[0]) - 0.5, "x1": int(n[-1]) + 0.5,
            "y0": 0, "y1": 0,
            "line": {"color": "rgba(148,163,184,0.4)", "width": 1, "dash": "dash"},
        }]

        return {"id": "impulse_response", "title": "Impulse Response h[n]", "data": traces, "layout": layout}

    def _make_magnitude_response_plot(self) -> Dict[str, Any]:
        """Compute and plot |H(e^jω)| on the unit circle."""
        omega = np.linspace(-np.pi, np.pi, 512)
        z_vals = np.exp(1j * omega)

        b_z = np.array(self._num_z, dtype=float)
        a_z = np.array(self._den_z, dtype=float)

        # Evaluate H(z) = B(z)/A(z)
        num_vals = np.polyval(b_z, z_vals)
        den_vals = np.polyval(a_z, z_vals)

        # Avoid division by zero
        with np.errstate(divide="ignore", invalid="ignore"):
            H = num_vals / den_vals
            H_mag = np.abs(H)
            H_mag = np.clip(H_mag, 0, 100)  # Clamp for display

        traces = [{
            "x": (omega / np.pi).tolist(),
            "y": H_mag.tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "#10b981", "width": 2},
            "name": "|H(e^jω)|",
            "hovertemplate": "ω/π = %{x:.3f}<br>|H| = %{y:.4g}<extra></extra>",
        }]

        layout = self._base_layout("ω/π", "|H(e^jω)|")
        layout["title"] = {"text": "Magnitude Response", "font": {"size": 14, "color": "#f1f5f9"}}
        layout["xaxis"]["range"] = [-1, 1]
        layout["xaxis"]["dtick"] = 0.25
        layout["yaxis"]["autorange"] = True
        layout["uirevision"] = self._revision_key("magnitude_response")

        return {"id": "magnitude_response", "title": "Magnitude Response", "data": traces, "layout": layout}

    # ── State ─────────────────────────────────────────────────────

    def get_state(self) -> Dict[str, Any]:
        if self._n is None:
            self._compute()

        state = super().get_state()

        # Solution steps: in solve mode, reveal up to current step
        mode = self.parameters.get("mode", "solve")
        if mode == "solve":
            visible_steps = self._solution_steps[:self._current_step + 1]
        else:
            visible_steps = self._solution_steps

        state["metadata"] = {
            "simulation_type": "inverse_z_transform",
            "sticky_controls": True,
            "current_step": self._current_step,
            "max_step": self.MAX_STEP,
            "solution_steps": visible_steps,
            "all_step_titles": [s["title"] for s in self._solution_steps],
            "active_method": self.parameters.get("active_method", "partial_fractions"),
            "mode": mode,
            "system_info": {
                "num_coeffs": self._num_z,
                "den_coeffs": self._den_z,
                "poles": [
                    {
                        "real": float(p.real),
                        "imag": float(p.imag),
                        "magnitude": float(abs(p)),
                        "angle_deg": float(np.degrees(np.angle(p))),
                    }
                    for p in self._poles
                ],
                "zeros": [
                    {"real": float(z.real), "imag": float(z.imag)}
                    for z in self._zeros
                ],
                "residues": [
                    {"real": float(r.real), "imag": float(r.imag)}
                    for r in self._residues
                ],
                "direct_terms": [float(np.real(d)) for d in self._direct_terms] if len(self._direct_terms) > 0 else [],
                "roc_regions": self._roc_regions,
                "is_stable": self._is_stable,
                "preset_description": self._get_preset_description(),
            },
            "method_b_steps": self._method_b_steps if self.parameters.get("active_method") == "long_division" else [],
            "method_c_terms": self._method_c_terms if self.parameters.get("active_method") == "power_series" else [],
            "quiz": {
                "active": self._quiz_active,
                "checked": self._quiz_checked,
                "scores": self._quiz_scores,
                "num_residues": len(self._residues),
            } if mode == "quiz" else None,
        }
        return state

    # ── Helpers ────────────────────────────────────────────────────

    def _revision_key(self, plot_id: str) -> str:
        """Generate a dynamic uirevision key so Plotly resets zoom/pan on changes."""
        preset = self.parameters.get("preset", "")
        roc = self.parameters.get("roc_type", "")
        method = self.parameters.get("active_method", "")
        nc = str(self.parameters.get("num_coeffs", ""))
        dc = str(self.parameters.get("den_coeffs", ""))
        step = self._current_step
        return f"{plot_id}-{preset}-{roc}-{method}-{step}-{nc}-{dc}"

    def _base_layout(self, xtitle: str, ytitle: str) -> Dict[str, Any]:
        return {
            "xaxis": {
                "title": xtitle,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "showgrid": True,
            },
            "yaxis": {
                "title": ytitle,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "showgrid": True,
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "legend": {
                "x": 1, "xanchor": "right",
                "y": 1, "yanchor": "top",
                "bgcolor": "rgba(0,0,0,0.3)",
                "font": {"size": 11, "color": "#f1f5f9"},
            },
        }

    @staticmethod
    def _fmt_complex(z: complex) -> str:
        """Format a complex number for display."""
        if abs(z.imag) < 1e-10:
            val = z.real
            if abs(val - round(val)) < 1e-10 and abs(val) < 1e6:
                return f"{int(round(val))}" if abs(val) >= 1 else f"{val:.4g}"
            return f"{val:.4g}"
        sign = "+" if z.imag >= 0 else "−"
        real_str = f"{z.real:.4g}"
        imag_str = f"{abs(z.imag):.4g}"
        return f"{real_str} {sign} {imag_str}j"

    @staticmethod
    def _format_poly(coeffs: List[float], var: str = "z") -> str:
        """Format polynomial coefficients as a readable string."""
        if not coeffs:
            return "0"
        degree = len(coeffs) - 1
        terms = []
        for i, c in enumerate(coeffs):
            power = degree - i
            if abs(c) < 1e-15:
                continue
            # Format coefficient
            if power == 0:
                terms.append(f"{c:.4g}")
            elif power == 1:
                if abs(c - 1.0) < 1e-10:
                    terms.append(var)
                elif abs(c + 1.0) < 1e-10:
                    terms.append(f"−{var}")
                else:
                    terms.append(f"{c:.4g}{var}")
            else:
                if abs(c - 1.0) < 1e-10:
                    terms.append(f"{var}^{power}")
                elif abs(c + 1.0) < 1e-10:
                    terms.append(f"−{var}^{power}")
                else:
                    terms.append(f"{c:.4g}{var}^{power}")

        if not terms:
            return "0"

        result = terms[0]
        for t in terms[1:]:
            if t.startswith("−"):
                result += f" − {t[1:]}"
            else:
                result += f" + {t}"
        return result

    def _get_preset_description(self) -> str:
        preset = self.parameters.get("preset", "example_1")
        if preset in self.PRESETS:
            return self.PRESETS[preset]["description"]
        return "Custom transfer function"
