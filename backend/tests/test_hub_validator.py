"""Tests for backend.core.hub_validator module.

Covers TF enrichment, SS enrichment, cross-derivation, stability checks,
system type detection, MIMO handling, discrete-time, and lightweight
slot validators.
"""

import numpy as np
import pytest

from core.hub_validator import (
    validate_and_enrich_control,
)


# -----------------------------------------------------------------------
# Transfer function source tests
# -----------------------------------------------------------------------

class TestTFFirstOrder:
    """First-order TF: G(s) = 1 / (s + 2). One real pole at -2, stable, type 0."""

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [1.0, 2.0],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_order(self) -> None:
        d = self.result["data"]
        assert d["order"] == 1

    def test_single_real_pole(self) -> None:
        poles = self.result["data"]["poles"]
        assert len(poles) == 1
        assert abs(poles[0]["real"] - (-2.0)) < 1e-8
        assert abs(poles[0]["imag"]) < 1e-8

    def test_no_zeros(self) -> None:
        assert len(self.result["data"]["zeros"]) == 0

    def test_stable(self) -> None:
        assert self.result["data"]["stable"] is True

    def test_type_zero(self) -> None:
        assert self.result["data"]["system_type"] == 0

    def test_domain_defaults_ct(self) -> None:
        assert self.result["data"]["domain"] == "ct"

    def test_dimensions_siso(self) -> None:
        dims = self.result["data"]["dimensions"]
        assert dims == {"n": 1, "m": 1, "p": 1}

    def test_ss_derived(self) -> None:
        assert "ss" in self.result["data"]
        ss = self.result["data"]["ss"]
        assert "A" in ss and "B" in ss and "C" in ss and "D" in ss

    def test_controllable_and_observable(self) -> None:
        d = self.result["data"]
        assert d["controllable"] is True
        assert d["observable"] is True

    def test_variable_is_s(self) -> None:
        assert self.result["data"]["tf"]["variable"] == "s"


class TestTFSecondOrderUnderdamped:
    """Second-order underdamped: G(s) = 1 / (s^2 + s + 1).

    Poles at -0.5 +/- j*sqrt(3)/2. Stable, type 0.
    """

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [1.0, 1.0, 1.0],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_order_two(self) -> None:
        assert self.result["data"]["order"] == 2

    def test_complex_poles(self) -> None:
        poles = self.result["data"]["poles"]
        assert len(poles) == 2
        # Both poles should have negative real part.
        for p in poles:
            assert p["real"] < 0
        # At least one should have nonzero imaginary part.
        imag_parts = [abs(p["imag"]) for p in poles]
        assert max(imag_parts) > 0.1

    def test_stable(self) -> None:
        assert self.result["data"]["stable"] is True

    def test_conjugate_pair(self) -> None:
        poles = self.result["data"]["poles"]
        # Imaginary parts should be conjugates.
        assert abs(poles[0]["imag"] + poles[1]["imag"]) < 1e-8


class TestTFUnstable:
    """Unstable system: G(s) = 1 / (s - 1). Pole at +1."""

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [1.0, -1.0],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_unstable(self) -> None:
        assert self.result["data"]["stable"] is False

    def test_pole_in_rhp(self) -> None:
        poles = self.result["data"]["poles"]
        assert len(poles) == 1
        assert poles[0]["real"] > 0


class TestTFTypeOne:
    """Type 1 system: G(s) = 1 / (s(s + 2)) = 1 / (s^2 + 2s)."""

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [1.0, 2.0, 0.0],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_type_one(self) -> None:
        assert self.result["data"]["system_type"] == 1

    def test_order_two(self) -> None:
        assert self.result["data"]["order"] == 2


class TestTFTypeTwo:
    """Type 2 system: G(s) = 1 / (s^2(s + 1)) = 1 / (s^3 + s^2)."""

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [1.0, 1.0, 0.0, 0.0],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_type_two(self) -> None:
        assert self.result["data"]["system_type"] == 2

    def test_order_three(self) -> None:
        assert self.result["data"]["order"] == 3


class TestTFZeroExtraction:
    """TF with zeros: G(s) = (s + 3) / (s^2 + 2s + 1).

    One zero at s = -3, poles at s = -1 (double).
    """

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0, 3.0],
            "den": [1.0, 2.0, 1.0],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_one_zero(self) -> None:
        zeros = self.result["data"]["zeros"]
        assert len(zeros) == 1
        assert abs(zeros[0]["real"] - (-3.0)) < 1e-8
        assert abs(zeros[0]["imag"]) < 1e-8

    def test_two_poles(self) -> None:
        poles = self.result["data"]["poles"]
        assert len(poles) == 2
        for p in poles:
            assert abs(p["real"] - (-1.0)) < 1e-6


class TestTFInvalidInput:
    """Invalid TF inputs."""

    def test_empty_den(self) -> None:
        result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [],
        })
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_missing_num(self) -> None:
        result = validate_and_enrich_control({
            "source": "tf",
            "den": [1.0, 1.0],
        })
        assert result["success"] is False

    def test_missing_den(self) -> None:
        result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
        })
        assert result["success"] is False

    def test_all_zero_den(self) -> None:
        result = validate_and_enrich_control({
            "source": "tf",
            "num": [1.0],
            "den": [0.0, 0.0],
        })
        assert result["success"] is False

    def test_invalid_source(self) -> None:
        result = validate_and_enrich_control({
            "source": "invalid",
        })
        assert result["success"] is False

    def test_not_a_dict(self) -> None:
        result = validate_and_enrich_control("not a dict")
        assert result["success"] is False


# -----------------------------------------------------------------------
# State-space source tests
# -----------------------------------------------------------------------

class TestSSToTFDerivation:
    """State-space SISO system with known TF.

    Controllable canonical form for G(s) = 1 / (s + 2):
    A = [[-2]], B = [[1]], C = [[1]], D = [[0]]
    """

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "ss",
            "A": [[-2.0]],
            "B": [[1.0]],
            "C": [[1.0]],
            "D": [[0.0]],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_tf_derived(self) -> None:
        d = self.result["data"]
        assert "tf" in d
        # Denominator should represent s + 2.
        den = d["tf"]["den"]
        assert len(den) == 2
        assert abs(den[0] - 1.0) < 1e-8
        assert abs(den[1] - 2.0) < 1e-8

    def test_poles_from_eigenvalues(self) -> None:
        poles = self.result["data"]["poles"]
        assert len(poles) == 1
        assert abs(poles[0]["real"] - (-2.0)) < 1e-8

    def test_stable(self) -> None:
        assert self.result["data"]["stable"] is True

    def test_controllable(self) -> None:
        assert self.result["data"]["controllable"] is True

    def test_observable(self) -> None:
        assert self.result["data"]["observable"] is True

    def test_source_is_ss(self) -> None:
        assert self.result["data"]["source"] == "ss"


class TestSSSecondOrder:
    """Second-order SS: companion form for s^2 + 3s + 2 = (s+1)(s+2).

    A = [[0, 1], [-2, -3]], B = [[0], [1]], C = [[1, 0]], D = [[0]]
    """

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "ss",
            "A": [[0, 1], [-2, -3]],
            "B": [[0], [1]],
            "C": [[1, 0]],
            "D": [[0]],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_order_two(self) -> None:
        assert self.result["data"]["order"] == 2

    def test_poles(self) -> None:
        poles = self.result["data"]["poles"]
        reals = sorted([p["real"] for p in poles])
        assert abs(reals[0] - (-2.0)) < 1e-6
        assert abs(reals[1] - (-1.0)) < 1e-6


class TestSSMIMO:
    """MIMO system (2 inputs, 2 outputs, 2 states).

    Should compute poles, controllability, observability, but NOT derive TF.
    """

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "ss",
            "A": [[-1, 0], [0, -2]],
            "B": [[1, 0], [0, 1]],
            "C": [[1, 0], [0, 1]],
            "D": [[0, 0], [0, 0]],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_dimensions(self) -> None:
        dims = self.result["data"]["dimensions"]
        assert dims["n"] == 2
        assert dims["m"] == 2
        assert dims["p"] == 2

    def test_no_tf_for_mimo(self) -> None:
        assert "tf" not in self.result["data"]

    def test_poles_from_eigenvalues(self) -> None:
        poles = self.result["data"]["poles"]
        reals = sorted([p["real"] for p in poles])
        assert abs(reals[0] - (-2.0)) < 1e-6
        assert abs(reals[1] - (-1.0)) < 1e-6

    def test_stable(self) -> None:
        assert self.result["data"]["stable"] is True

    def test_controllable(self) -> None:
        assert self.result["data"]["controllable"] is True

    def test_observable(self) -> None:
        assert self.result["data"]["observable"] is True


class TestSSInvalidDimensions:
    """Invalid SS matrix dimensions."""

    def test_non_square_A(self) -> None:
        result = validate_and_enrich_control({
            "source": "ss",
            "A": [[1, 2, 3], [4, 5, 6]],
            "B": [[1], [1]],
            "C": [[1, 0]],
            "D": [[0]],
        })
        assert result["success"] is False
        assert "square" in result["error"].lower()

    def test_missing_matrix(self) -> None:
        result = validate_and_enrich_control({
            "source": "ss",
            "A": [[-1]],
            "B": [[1]],
            "C": [[1]],
        })
        assert result["success"] is False
        assert "'D'" in result["error"]


# -----------------------------------------------------------------------
# Discrete-time tests
# -----------------------------------------------------------------------

class TestDTStable:
    """DT stable system: G(z) = 1 / (z - 0.5). Pole at 0.5 inside unit circle."""

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "domain": "dt",
            "num": [1.0],
            "den": [1.0, -0.5],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_stable(self) -> None:
        assert self.result["data"]["stable"] is True

    def test_domain(self) -> None:
        assert self.result["data"]["domain"] == "dt"

    def test_variable_z(self) -> None:
        assert self.result["data"]["tf"]["variable"] == "z"

    def test_pole_inside_unit_circle(self) -> None:
        poles = self.result["data"]["poles"]
        assert len(poles) == 1
        assert abs(poles[0]["real"] - 0.5) < 1e-8


class TestDTUnstable:
    """DT unstable system: G(z) = 1 / (z - 1.5). Pole at 1.5 outside unit circle."""

    def setup_method(self) -> None:
        self.result = validate_and_enrich_control({
            "source": "tf",
            "domain": "dt",
            "num": [1.0],
            "den": [1.0, -1.5],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_unstable(self) -> None:
        assert self.result["data"]["stable"] is False

    def test_pole_outside_unit_circle(self) -> None:
        poles = self.result["data"]["poles"]
        assert abs(poles[0]["real"] - 1.5) < 1e-8


class TestDTTypeOne:
    """DT type 1 system: pole at z = 1. G(z) = 1 / ((z - 1)(z - 0.5))."""

    def setup_method(self) -> None:
        # (z - 1)(z - 0.5) = z^2 - 1.5z + 0.5
        self.result = validate_and_enrich_control({
            "source": "tf",
            "domain": "dt",
            "num": [1.0],
            "den": [1.0, -1.5, 0.5],
        })

    def test_success(self) -> None:
        assert self.result["success"] is True

    def test_type_one(self) -> None:
        assert self.result["data"]["system_type"] == 1


# -----------------------------------------------------------------------
# Block diagram pass-through
# -----------------------------------------------------------------------

class TestBlockDiagramPassthrough:
    """Block diagram source should pass through without enrichment."""

    def test_passthrough(self) -> None:
        data = {"source": "block_diagram", "nodes": [1, 2], "edges": [(1, 2)]}
        result = validate_and_enrich_control(data)
        assert result["success"] is True
        assert result["data"]["source"] == "block_diagram"
        assert result["data"]["nodes"] == [1, 2]
        assert result["data"]["domain"] == "ct"


