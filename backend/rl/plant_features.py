"""Extract compact plant features for RL/ES policies."""
from __future__ import annotations

import numpy as np


def extract_plant_features(
    plant_num: np.ndarray,
    plant_den: np.ndarray,
    fopdt_params: tuple[float, float, float] | None = None,
) -> np.ndarray:
    """Extract 8-dimensional plant feature vector.

    Features (all normalized to roughly [-1, 1]):
        [0] K_fopdt     — FOPDT gain (log-scaled)
        [1] tau_fopdt   — FOPDT time constant (log-scaled)
        [2] L_fopdt     — FOPDT dead time (log-scaled)
        [3] plant_order — polynomial order / 5
        [4] n_unstable  — fraction of RHP poles
        [5] dom_pole_re — dominant pole real part / 20
        [6] dom_pole_im — dominant pole imaginary part / 20
        [7] dc_gain     — DC gain at s=0 (log-scaled)
    """
    K, tau, L = fopdt_params if fopdt_params is not None else (1.0, 1.0, 0.1)

    # Plant poles
    poles = np.roots(plant_den)
    order = max(len(poles), 1)
    n_unstable = int(np.sum(poles.real > 0))

    # Dominant pole (largest real part)
    if len(poles) > 0:
        dom_idx = int(np.argmax(poles.real))
        dom_re = float(poles[dom_idx].real)
        dom_im = float(poles[dom_idx].imag)
    else:
        dom_re, dom_im = 0.0, 0.0

    # DC gain: G(0) = num(0)/den(0)
    try:
        dc = float(np.polyval(plant_num, 0) / np.polyval(plant_den, 0))
        dc = np.clip(dc, -100, 100)
    except (ZeroDivisionError, FloatingPointError):
        dc = 0.0

    features = np.array([
        np.log1p(abs(K)) * np.sign(K) / 4.0,
        np.log1p(abs(tau)) / 3.0,
        np.log1p(abs(L)) / 3.0,
        min(order, 5) / 5.0,
        n_unstable / max(order, 1),
        np.clip(dom_re, -20, 5) / 20.0,
        np.clip(dom_im, -20, 20) / 20.0,
        np.clip(np.log1p(abs(dc)) * np.sign(dc), -5, 5) / 5.0,
    ], dtype=np.float64)

    return features
