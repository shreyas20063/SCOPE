"""Block Diagram Builder: continuous-time expressions are rejected in DT mode.

Before this fix, an s-domain (or A-operator) custom TF typed in DT mode was
"converted" by reusing its A-domain coefficients as R-domain coefficients.
That is the substitution z = s: 1/(s+1) became H(z) = 1/(z+1) (marginal),
1/(s+2) became 1/(z+2) (unstable), 1/(s-0.5) became 1/(z-0.5) (stable).
A valid CT->DT map needs a sampling period T (z = e^{pT}, Tustin, Euler),
which the builder does not have. DT mode now rejects s/A expressions, just
as CT mode rejects z/R expressions.

handle_action() catches every exception into self._error, so these tests
assert on sim._error and on the block contents, never on raised exceptions.
Run from backend/:  python -m pytest tests/test_bdb_dt_domain_rejection.py
"""

from typing import Dict, List, Optional, Tuple

import pytest

from core.executor import ExecutionError
from simulations.block_diagram_builder import BlockDiagramSimulator


def _add_block(sim: BlockDiagramSimulator, block_type: str) -> str:
    """Add a block and return its new id."""
    before = set(sim.blocks)
    sim.handle_action("add_block", {"block_type": block_type, "position": {"x": 0, "y": 0}})
    # _error may hold an incomplete-diagram message here; check the block itself.
    new_ids = set(sim.blocks) - before
    assert len(new_ids) == 1, f"add_block({block_type}) failed: {sim._error}"
    return new_ids.pop()


def _build(system_type: str) -> Tuple[BlockDiagramSimulator, str]:
    """Build input -> custom_tf -> output in the given mode; return (sim, ctf_id)."""
    sim = BlockDiagramSimulator("block_diagram_builder")
    sim.initialize({"system_type": system_type})
    sim.handle_action("set_system_type", {"system_type": system_type})
    assert sim.system_type == system_type
    inp = _add_block(sim, "input")
    ctf = _add_block(sim, "custom_tf")
    out = _add_block(sim, "output")
    sim.handle_action("add_connection", {"from_block": inp, "from_port": 0, "to_block": ctf, "to_port": 0})
    sim.handle_action("add_connection", {"from_block": ctf, "from_port": 1, "to_block": out, "to_port": 0})
    assert sim._error is None, sim._error
    assert len(sim.connections) == 2
    return sim, ctf


def _set_expr(sim: BlockDiagramSimulator, ctf: str, expr: str) -> Dict:
    return sim.handle_action("update_block_value", {"block_id": ctf, "value": expr})


def _pole_list(sim: BlockDiagramSimulator) -> List[complex]:
    tf = sim._tf_result
    assert tf is not None, f"no TF computed (error: {sim._error})"
    return sorted(
        (complex(p["real"], p["imag"]) for p in tf["poles"]),
        key=lambda c: (c.real, c.imag),
    )


def _snapshot(block: Dict) -> Tuple[str, List[float], List[float], Optional[str]]:
    return (
        block["expression"],
        list(block["num_coeffs"]),
        list(block["den_coeffs"]),
        block.get("converted_from"),
    )


# ---------------------------------------------------------------------------
# DT mode rejects s- and A-domain expressions
# ---------------------------------------------------------------------------

CT_EXPRESSIONS = ["1/(s+1)", "(s+1)/(s^2+3s+2)", "A/(1+2A)"]


@pytest.mark.parametrize("expr", CT_EXPRESSIONS)
def test_dt_rejects_ct_expression_on_fresh_block(expr: str) -> None:
    sim, ctf = _build("dt")
    before = _snapshot(sim.blocks[ctf])
    tf_before = sim._tf_result

    state = _set_expr(sim, ctf, expr)

    assert sim._error is not None, f"DT mode accepted {expr!r}"
    assert "sampling period" in sim._error
    assert "discrete-time" in sim._error
    assert state["metadata"]["error"] == sim._error
    assert _snapshot(sim.blocks[ctf]) == before
    assert sim.blocks[ctf]["expression"] == "1"
    assert sim._tf_result is tf_before


@pytest.mark.parametrize("expr", CT_EXPRESSIONS)
def test_dt_rejection_keeps_previous_valid_expression(expr: str) -> None:
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, "1/(1-0.5R)")
    assert sim._error is None, sim._error
    before = _snapshot(sim.blocks[ctf])
    poles_before = _pole_list(sim)

    _set_expr(sim, ctf, expr)

    assert sim._error is not None
    assert "sampling period" in sim._error
    assert _snapshot(sim.blocks[ctf]) == before
    assert _pole_list(sim) == poles_before
    assert abs(poles_before[0] - 0.5) < 1e-9


def test_dt_s_error_names_valid_alternatives() -> None:
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, "1/(s+1)")
    msg = sim._error
    assert msg.startswith("Cannot use s-domain expression in discrete-time mode.")
    assert "z^-1" in msg and " R" in msg
    assert "CT/DT Poles Conversion" in msg


def test_dt_a_error_explains_integrator_vs_delay() -> None:
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, "A/(1+2A)")
    msg = sim._error
    assert msg.startswith("Cannot use A-domain expression in discrete-time mode.")
    assert "integrator" in msg
    assert "sampling period" in msg


def test_dt_rejects_before_parsing_malformed_s_expression() -> None:
    """A malformed s-expression gets the domain error, not a parse error."""
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, "1/(s+1")
    assert sim._error is not None
    assert "sampling period" in sim._error


# ---------------------------------------------------------------------------
# DT mode still accepts R / z / z^-1 expressions with correct poles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "expr, expected_conv",
    [("1/(1-0.5R)", None), ("z/(z-0.5)", "z"), ("1/(1-0.5z^-1)", "z")],
)
def test_dt_accepts_discrete_expressions(expr: str, expected_conv: Optional[str]) -> None:
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, expr)
    assert sim._error is None, f"{expr!r} rejected: {sim._error}"
    block = sim.blocks[ctf]
    assert block["expression"] == expr
    assert block.get("converted_from") == expected_conv
    # All three are H(R) = 1/(1 - 0.5R) = z/(z - 0.5)
    assert block["num_coeffs"] == [1.0, 0.0] or block["num_coeffs"] == [1.0]
    assert block["den_coeffs"] == [1.0, -0.5]
    poles = _pole_list(sim)
    assert len(poles) == 1
    assert abs(poles[0] - 0.5) < 1e-9
    assert sim._tf_result["stability"] == "stable"
    assert sim._tf_result["operator"] == "R"


def test_dt_constant_expression_still_accepted() -> None:
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, "2")
    assert sim._error is None, sim._error
    assert sim.blocks[ctf]["num_coeffs"] == [2.0]
    assert sim.blocks[ctf]["den_coeffs"] == [1.0]


# ---------------------------------------------------------------------------
# CT mode unchanged
# ---------------------------------------------------------------------------

def test_ct_still_converts_s_to_a() -> None:
    sim, ctf = _build("ct")
    _set_expr(sim, ctf, "1/(s+2)")
    assert sim._error is None, sim._error
    block = sim.blocks[ctf]
    assert block["converted_from"] == "s"
    # 1/(s+2) = A/(1+2A), low-power-first in A
    assert block["num_coeffs"] == [0.0, 1.0]
    assert block["den_coeffs"] == [1.0, 2.0]
    poles = _pole_list(sim)
    assert len(poles) == 1
    assert abs(poles[0] - (-2.0)) < 1e-9
    assert sim._tf_result["stability"] == "stable"
    assert sim._tf_result["operator"] == "A"


def test_ct_still_accepts_a_expression() -> None:
    sim, ctf = _build("ct")
    _set_expr(sim, ctf, "A/(1+2A)")
    assert sim._error is None, sim._error
    poles = _pole_list(sim)
    assert len(poles) == 1
    assert abs(poles[0] - (-2.0)) < 1e-9


def test_ct_still_rejects_z_expression() -> None:
    sim, ctf = _build("ct")
    before = _snapshot(sim.blocks[ctf])
    _set_expr(sim, ctf, "z/(z-0.5)")
    assert sim._error == (
        "Cannot use z-domain expression in continuous-time mode. "
        "Use 's' or 'A' as the variable."
    )
    assert _snapshot(sim.blocks[ctf]) == before


# ---------------------------------------------------------------------------
# Paths that used to move an existing block across domains without
# re-parsing it. Undo/redo now restore the system type with the blocks and
# update_parameter('system_type') clears the diagram, so a custom-TF block
# always stays in the mode it was parsed in. tests/test_bdb_history_domain.py
# covers these paths (and delay/integrator blocks) in depth.
# ---------------------------------------------------------------------------

def _ct_block_with_s_expression() -> Tuple[BlockDiagramSimulator, str]:
    sim, ctf = _build("ct")
    _set_expr(sim, ctf, "1/(s+2)")
    assert sim._error is None, sim._error
    return sim, ctf


def _assert_ct_block_back_in_ct(sim: BlockDiagramSimulator, ctf: str) -> None:
    assert sim.system_type == "ct"
    assert sim.parameters["system_type"] == "ct"
    assert sim._error is None, sim._error
    assert sim.blocks[ctf]["expression"] == "1/(s+2)"
    assert sim._tf_result["operator"] == "A"
    poles = _pole_list(sim)
    # 1/(s+2): pole s = -2, not the z = s reading 1/(z+2) (pole z = -2).
    assert len(poles) == 1
    assert abs(poles[0] - (-2.0)) < 1e-9
    assert sim._tf_result["stability"] == "stable"
    hub = sim.to_hub_data()
    assert hub["domain"] == "ct"
    assert hub["tf"]["variable"] == "s"


def _assert_stale_ct_block_flagged(sim: BlockDiagramSimulator) -> None:
    assert sim.system_type == "dt"
    assert sim._error is not None, "s-domain block silently used as R-coefficients"
    assert "1/(s+2)" in sim._error
    assert "sampling period" in sim._error
    # No TF: in particular not the old z = s result 1/(z+2), and not a silent 0.
    assert sim._tf_result is None
    meta = sim.get_state()["metadata"]
    assert meta["tf_error_kind"] == "domain"
    assert meta["domain_error"] == sim._error
    # Exports are refused instead of shipping the block under domain 'dt'.
    with pytest.raises(ExecutionError):
        sim.to_hub_data()


def test_undo_across_system_type_switch_restores_ct_block_in_ct() -> None:
    sim, ctf = _ct_block_with_s_expression()
    sim.handle_action("set_system_type", {"system_type": "dt"})
    assert sim._error is None
    assert sim.blocks == {}
    sim.handle_action("undo", {})
    _assert_ct_block_back_in_ct(sim, ctf)


def test_undo_after_dt_preset_restores_ct_block_in_ct() -> None:
    sim, ctf = _ct_block_with_s_expression()
    sim.handle_action("load_preset", {"preset": "accumulator"})
    assert sim._error is None, sim._error
    assert sim.system_type == "dt"
    sim.handle_action("undo", {})
    _assert_ct_block_back_in_ct(sim, ctf)


def test_update_parameter_system_type_clears_ct_block() -> None:
    sim, _ = _ct_block_with_s_expression()
    sim.update_parameter("system_type", "dt")
    assert sim.system_type == "dt"
    assert sim.blocks == {}
    assert sim.connections == []
    assert sim._tf_result is None
    assert sim._error is None
    assert "tf" not in sim.to_hub_data()


def test_stale_ct_block_in_dt_is_flagged_and_recovers() -> None:
    """No action can put an s-block into DT any more; force the state to
    exercise the guard in _compute_transfer_function and to_hub_data."""
    sim, ctf = _ct_block_with_s_expression()
    sim.system_type = "dt"
    sim.parameters["system_type"] = "dt"
    sim._recompute_tf()
    _assert_stale_ct_block_flagged(sim)
    _set_expr(sim, ctf, "z/(z-0.5)")
    assert sim._error is None, sim._error
    poles = _pole_list(sim)
    assert len(poles) == 1
    assert abs(poles[0] - 0.5) < 1e-9
    assert sim.get_state()["metadata"]["domain_error"] is None


def test_undo_dt_to_ct_switch_restores_dt_block_in_dt() -> None:
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, "z/(z-0.5)")
    assert sim._error is None, sim._error
    sim.handle_action("set_system_type", {"system_type": "ct"})
    sim.handle_action("undo", {})
    assert sim.system_type == "dt"
    assert sim._error is None, sim._error
    assert sim._tf_result["operator"] == "R"
    poles = _pole_list(sim)
    assert len(poles) == 1
    assert abs(poles[0] - 0.5) < 1e-9


def test_dt_block_forced_into_ct_is_flagged() -> None:
    sim, ctf = _build("dt")
    _set_expr(sim, ctf, "z/(z-0.5)")
    sim.system_type = "ct"
    sim.parameters["system_type"] = "ct"
    sim._recompute_tf()
    assert sim._error is not None
    assert "continuous-time" in sim._error
    assert sim._tf_result is None
