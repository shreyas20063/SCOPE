"""Block Diagram Builder: undo/redo, system-type changes and edit errors keep
every block in the CT/DT domain it was built in.

Delay (R) and Integrator (A) are both [0, 1] in _block_tf, and custom-TF
coefficients are R- or A-polynomials, so a block restored into the other
domain is silently read in the wrong operator. Before this fix:

* undo/redo snapshots held (blocks, connections, next_id) but not
  system_type: undo after a CT->DT switch (or a DT preset) brought the CT
  blocks back while the mode stayed DT, so integrators became delays;
* update_parameter('system_type') changed the domain but kept the blocks;
* a rejected update_block_value pushed an undo entry and cleared redo;
* the TF dialog could not tell a rejected edit from an accepted edit
  whose recompute failed ('No input block found' on an unwired block).

handle_action() catches every exception into self._error, so these tests
assert on state and metadata, never on raised exceptions.
Run from backend/:  python -m pytest tests/test_bdb_history_domain.py
"""

import uuid
from typing import Dict, List, Tuple

import pytest

from core.executor import ExecutionError
from simulations.block_diagram_builder import BlockDiagramSimulator

TOL = 1e-9


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_block(sim: BlockDiagramSimulator, block_type: str) -> str:
    """Add a block and return its new id."""
    before = set(sim.blocks)
    sim.handle_action("add_block", {"block_type": block_type, "position": {"x": 0, "y": 0}})
    new_ids = set(sim.blocks) - before
    assert len(new_ids) == 1, f"add_block({block_type}) failed: {sim._error}"
    return new_ids.pop()


def _connect(sim: BlockDiagramSimulator, src: str, dst: str, from_port: int = 1) -> None:
    n = len(sim.connections)
    sim.handle_action("add_connection", {
        "from_block": src, "from_port": from_port, "to_block": dst, "to_port": 0,
    })
    assert len(sim.connections) == n + 1, f"connection {src}->{dst} failed: {sim._error}"


def _fresh(system_type: str) -> BlockDiagramSimulator:
    sim = BlockDiagramSimulator("block_diagram_builder")
    sim.initialize({"system_type": system_type})
    assert sim.system_type == system_type
    return sim


def _ct_integrator_diagram() -> Tuple[BlockDiagramSimulator, Dict[str, str]]:
    """CT: input -> integrator -> custom_tf 1/(s+2) -> output, H(s) = 1/(s(s+2))."""
    sim = _fresh("ct")
    ids = {
        "inp": _add_block(sim, "input"),
        "integ": _add_block(sim, "integrator"),
        "ctf": _add_block(sim, "custom_tf"),
        "out": _add_block(sim, "output"),
    }
    _connect(sim, ids["inp"], ids["integ"], from_port=0)
    _connect(sim, ids["integ"], ids["ctf"])
    _connect(sim, ids["ctf"], ids["out"])
    sim.handle_action("update_block_value", {"block_id": ids["ctf"], "value": "1/(s+2)"})
    assert sim._error is None, sim._error
    assert len(sim.connections) == 3
    _assert_ct_integrator_tf(sim)
    return sim, ids


def _poles(sim: BlockDiagramSimulator) -> List[complex]:
    tf = sim._tf_result
    assert tf is not None, f"no TF computed (error: {sim._error})"
    return sorted((complex(p["real"], p["imag"]) for p in tf["poles"]),
                  key=lambda c: (c.real, c.imag))


def _assert_ct_integrator_tf(sim: BlockDiagramSimulator) -> None:
    """H(s) = 1/(s(s+2)) in CT: A operator, poles at s = -2 and s = 0."""
    assert sim.system_type == "ct"
    assert sim.parameters["system_type"] == "ct"
    assert sim._error is None, sim._error
    tf = sim._tf_result
    assert tf["operator"] == "A"
    # Low-power-first in A: A^2 / (1 + 2A)  ==  1 / (s^2 + 2s)
    assert tf["numerator"] == pytest.approx([0.0, 0.0, 1.0])
    assert tf["denominator"] == pytest.approx([1.0, 2.0])
    poles = _poles(sim)
    assert len(poles) == 2
    assert abs(poles[0] - (-2.0)) < TOL
    assert abs(poles[1]) < TOL
    # One pole on the jw axis (the integrator): marginally stable, never the
    # 'unstable' that 1/(z+2) gives when A is read as R.
    assert tf["stability"] == "marginally_stable"
    meta = sim.get_state()["metadata"]
    assert meta["system_type"] == "ct"
    assert meta["hub_domain"] == "ct"
    assert meta["block_types"]["integrator"]["available"] is True
    assert meta["block_types"]["delay"]["available"] is False
    assert meta["domain_error"] is None
    hub = sim.to_hub_data()
    assert hub["domain"] == "ct"
    assert hub["tf"]["variable"] == "s"
    assert hub["tf"]["num"] == pytest.approx([1.0])
    assert hub["tf"]["den"] == pytest.approx([1.0, 2.0, 0.0])


def _assert_empty(sim: BlockDiagramSimulator, system_type: str) -> None:
    assert sim.system_type == system_type
    assert sim.parameters["system_type"] == system_type
    assert sim.blocks == {}
    assert sim.connections == []
    assert sim._tf_result is None
    assert sim._error is None
    meta = sim.get_state()["metadata"]
    assert meta["system_type"] == system_type
    assert meta["tf_error"] is None


def _block_types(sim: BlockDiagramSimulator) -> List[str]:
    return sorted(b["type"] for b in sim.blocks.values())


# ---------------------------------------------------------------------------
# 1. Undo/redo restore the system type together with the blocks
# ---------------------------------------------------------------------------

def test_undo_ct_to_dt_switch_returns_to_ct_with_correct_tf() -> None:
    sim, _ = _ct_integrator_diagram()
    sim.handle_action("set_system_type", {"system_type": "dt"})
    _assert_empty(sim, "dt")

    sim.handle_action("undo", {})

    assert _block_types(sim) == ["custom_tf", "input", "integrator", "output"]
    _assert_ct_integrator_tf(sim)


def test_redo_ct_to_dt_switch_returns_to_empty_dt() -> None:
    sim, _ = _ct_integrator_diagram()
    sim.handle_action("set_system_type", {"system_type": "dt"})
    sim.handle_action("undo", {})
    _assert_ct_integrator_tf(sim)

    sim.handle_action("redo", {})
    _assert_empty(sim, "dt")

    # And back again: the round trip is stable.
    sim.handle_action("undo", {})
    _assert_ct_integrator_tf(sim)


def test_undo_dt_to_ct_switch_keeps_delay_a_delay() -> None:
    """y[n] = x[n] + 0.5 y[n-1]: pole z = 0.5. Read in CT, the delay becomes an
    integrator and H = 1/(1 - 0.5A) = s/(s - 0.5), an unstable s-pole."""
    sim = _fresh("dt")
    sim.handle_action("load_preset", {"preset": "first_order_dt"})
    assert sim._error is None, sim._error
    poles_before = _poles(sim)
    assert len(poles_before) == 1 and abs(poles_before[0] - 0.5) < TOL

    sim.handle_action("set_system_type", {"system_type": "ct"})
    _assert_empty(sim, "ct")
    sim.handle_action("undo", {})

    assert sim.system_type == "dt"
    assert sim.parameters["system_type"] == "dt"
    assert "delay" in _block_types(sim)
    assert sim._error is None, sim._error
    assert sim._tf_result["operator"] == "R"
    assert sim._tf_result["stability"] == "stable"
    poles = _poles(sim)
    assert len(poles) == 1 and abs(poles[0] - 0.5) < TOL
    assert sim.to_hub_data()["domain"] == "dt"


def test_undo_dt_preset_returns_to_ct_diagram() -> None:
    sim, _ = _ct_integrator_diagram()
    sim.handle_action("load_preset", {"preset": "accumulator"})
    assert sim._error is None, sim._error
    assert sim.system_type == "dt"

    sim.handle_action("undo", {})
    assert _block_types(sim) == ["custom_tf", "input", "integrator", "output"]
    _assert_ct_integrator_tf(sim)

    sim.handle_action("redo", {})
    assert sim.system_type == "dt"
    assert sim.parameters["system_type"] == "dt"
    assert "integrator" not in _block_types(sim)
    assert sim._error is None, sim._error
    # Accumulator 1/(1 - R): pole z = 1.
    poles = _poles(sim)
    assert len(poles) == 1 and abs(poles[0] - 1.0) < TOL


def test_undo_ct_preset_returns_to_dt_diagram() -> None:
    sim = _fresh("dt")
    sim.handle_action("load_preset", {"preset": "first_order_dt"})
    sim.handle_action("load_preset", {"preset": "first_order_ct"})
    assert sim.system_type == "ct"
    sim.handle_action("undo", {})
    assert sim.system_type == "dt"
    assert "integrator" not in _block_types(sim)
    poles = _poles(sim)
    assert len(poles) == 1 and abs(poles[0] - 0.5) < TOL


def test_history_entries_record_system_type() -> None:
    sim, _ = _ct_integrator_diagram()
    sim.handle_action("set_system_type", {"system_type": "dt"})
    assert all(entry["system_type"] == "ct" for entry in sim._history)
    sim.handle_action("undo", {})
    assert [entry["system_type"] for entry in sim._redo_history] == ["dt"]


# ---------------------------------------------------------------------------
# 2. update_parameter('system_type') clears like the CT/DT toggle
# ---------------------------------------------------------------------------

def test_update_parameter_system_type_change_clears_diagram() -> None:
    sim, _ = _ct_integrator_diagram()
    history_len = len(sim._history)

    state = sim.update_parameter("system_type", "dt")

    _assert_empty(sim, "dt")
    assert state["metadata"]["blocks"] == {}
    assert state["metadata"]["system_type"] == "dt"
    assert state["parameters"]["system_type"] == "dt"
    assert len(sim._history) == history_len + 1


def test_update_parameter_system_type_change_is_undoable() -> None:
    sim, _ = _ct_integrator_diagram()
    sim.update_parameter("system_type", "dt")
    sim.handle_action("undo", {})
    _assert_ct_integrator_tf(sim)


def test_update_parameter_same_system_type_keeps_diagram() -> None:
    """An /update naming the current domain (e.g. a shared-link restore) is
    idempotent: it must not wipe the diagram the user has started building."""
    sim = _fresh("ct")
    sim.handle_action("set_system_type", {"system_type": "dt"})
    delay = _add_block(sim, "delay")
    history_len = len(sim._history)

    sim.update_parameter("system_type", "dt")

    assert delay in sim.blocks
    assert sim.system_type == "dt"
    assert len(sim._history) == history_len


def test_update_parameter_mode_still_works() -> None:
    sim, _ = _ct_integrator_diagram()
    sim.update_parameter("mode", "parse")
    assert sim.mode == "parse"
    assert sim.parameters["mode"] == "parse"
    _assert_ct_integrator_tf(sim)


def test_update_endpoint_clears_cross_domain_blocks() -> None:
    """Same path the web frontend and validation scripts use (/update)."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    headers = {"X-Session-ID": f"test-bdb-domain-{uuid.uuid4().hex[:12]}"}
    base = "/api/simulations/block_diagram_builder"

    def execute(action: str, params: Dict) -> Dict:
        resp = client.post(f"{base}/execute", headers=headers,
                           json={"action": action, "params": params})
        assert resp.status_code == 200, resp.text
        return resp.json()["data"]["metadata"]

    execute("set_system_type", {"system_type": "ct"})
    meta = execute("add_block", {"block_type": "integrator", "position": {"x": 0, "y": 0}})
    assert [b["type"] for b in meta["blocks"].values()] == ["integrator"]

    resp = client.post(f"{base}/update", headers=headers, json={"params": {"system_type": "dt"}})
    assert resp.status_code == 200, resp.text
    meta = resp.json()["data"]["metadata"]
    assert meta["system_type"] == "dt"
    assert meta["blocks"] == {}

    meta = execute("undo", {})
    assert meta["system_type"] == "ct"
    assert [b["type"] for b in meta["blocks"].values()] == ["integrator"]
    assert meta["domain_error"] is None


# ---------------------------------------------------------------------------
# parse_tf switches the domain only after it has parsed successfully
# ---------------------------------------------------------------------------

def test_failed_parse_keeps_current_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    sim, _ = _ct_integrator_diagram()
    blocks_before = sim.get_state()["metadata"]["blocks"]
    history_len = len(sim._history)

    def boom(expr: str, var: str):
        raise ValueError("unparseable")

    monkeypatch.setattr(sim, "_parse_ratio", boom)
    sim.handle_action("parse_tf", {"tf_string": "1/(1-0.5R)"})

    assert sim._error == "Could not parse expression: unparseable"
    assert sim.get_state()["metadata"]["last_action_error"] == sim._error
    assert len(sim._history) == history_len
    assert sim.blocks == blocks_before
    sim._error = None
    _assert_ct_integrator_tf(sim)


def test_successful_parse_switches_domain_and_is_undoable() -> None:
    sim, _ = _ct_integrator_diagram()
    sim.handle_action("parse_tf", {"tf_string": "1/(1-0.5R)"})
    assert sim._error is None, sim._error
    assert sim.system_type == "dt"
    poles = _poles(sim)
    assert len(poles) == 1 and abs(poles[0] - 0.5) < TOL
    sim.handle_action("undo", {})
    _assert_ct_integrator_tf(sim)


# ---------------------------------------------------------------------------
# 4. A rejected edit vs an accepted edit whose TF recompute fails
# ---------------------------------------------------------------------------

def test_accepted_edit_on_unwired_block_is_not_an_action_error() -> None:
    sim = _fresh("dt")
    ctf = _add_block(sim, "custom_tf")

    state = sim.handle_action("update_block_value", {"block_id": ctf, "value": "z/(z-0.5)"})

    meta = state["metadata"]
    assert sim.blocks[ctf]["expression"] == "z/(z-0.5)"
    assert sim.blocks[ctf]["den_coeffs"] == [1.0, -0.5]
    assert meta["last_action_error"] is None
    assert meta["error"] == "No input block found. Add an Input block."
    assert meta["tf_error"] == "No input block found. Add an Input block."
    assert meta["tf_error_kind"] == "incomplete"
    assert meta["transfer_function"] is None


def test_rejected_edit_on_unwired_block_is_an_action_error() -> None:
    sim = _fresh("dt")
    ctf = _add_block(sim, "custom_tf")

    state = sim.handle_action("update_block_value", {"block_id": ctf, "value": "1/(s+1)"})

    meta = state["metadata"]
    assert sim.blocks[ctf]["expression"] == "1"
    assert meta["last_action_error"] is not None
    assert "sampling period" in meta["last_action_error"]
    assert meta["error"] == meta["last_action_error"]
    # The diagram's own reason is unchanged and still reported.
    assert meta["tf_error"] == "No input block found. Add an Input block."
    assert meta["tf_error_kind"] == "incomplete"


def test_next_successful_action_clears_last_action_error() -> None:
    sim = _fresh("dt")
    ctf = _add_block(sim, "custom_tf")
    sim.handle_action("update_block_value", {"block_id": ctf, "value": "1/(s+1)"})
    assert sim.get_state()["metadata"]["last_action_error"] is not None
    sim.handle_action("update_block_value", {"block_id": ctf, "value": "1/(1-0.5R)"})
    assert sim.get_state()["metadata"]["last_action_error"] is None


def test_tf_error_clears_once_diagram_is_complete() -> None:
    sim = _fresh("dt")
    inp = _add_block(sim, "input")
    ctf = _add_block(sim, "custom_tf")
    assert sim.get_state()["metadata"]["tf_error_kind"] == "incomplete"
    out = _add_block(sim, "output")
    _connect(sim, inp, ctf, from_port=0)
    _connect(sim, ctf, out)
    meta = sim.get_state()["metadata"]
    assert meta["tf_error"] is None
    assert meta["tf_error_kind"] is None
    assert meta["transfer_function"] is not None


# ---------------------------------------------------------------------------
# 5. Rejected actions leave undo/redo untouched
# ---------------------------------------------------------------------------

def _wired_dt_custom_tf() -> Tuple[BlockDiagramSimulator, str]:
    sim = _fresh("dt")
    inp = _add_block(sim, "input")
    ctf = _add_block(sim, "custom_tf")
    out = _add_block(sim, "output")
    _connect(sim, inp, ctf, from_port=0)
    _connect(sim, ctf, out)
    assert sim._error is None, sim._error
    return sim, ctf


@pytest.mark.parametrize("bad", ["1/(s+1)", "A/(1+2A)", "", "x" * 201])
def test_rejected_custom_tf_edit_adds_no_undo_entry(bad: str) -> None:
    sim, ctf = _wired_dt_custom_tf()
    sim.handle_action("update_block_value", {"block_id": ctf, "value": "z/(z-0.5)"})
    assert sim._error is None, sim._error
    history_len = len(sim._history)

    sim.handle_action("update_block_value", {"block_id": ctf, "value": bad})

    assert sim._error is not None
    assert len(sim._history) == history_len
    assert sim.blocks[ctf]["expression"] == "z/(z-0.5)"
    # One undo goes straight back past the valid edit, not to a duplicate.
    sim.handle_action("undo", {})
    assert sim._error is None, sim._error
    assert sim.blocks[ctf]["expression"] == "1"


def test_rejected_edit_keeps_redo_stack() -> None:
    sim, ctf = _wired_dt_custom_tf()
    sim.handle_action("update_block_value", {"block_id": ctf, "value": "z/(z-0.5)"})
    sim.handle_action("undo", {})
    assert sim.blocks[ctf]["expression"] == "1"
    assert len(sim._redo_history) == 1

    sim.handle_action("update_block_value", {"block_id": ctf, "value": "1/(s+1)"})
    assert sim._error is not None

    assert len(sim._redo_history) == 1
    sim.handle_action("redo", {})
    assert sim._error is None, sim._error
    assert sim.blocks[ctf]["expression"] == "z/(z-0.5)"


def test_rejected_gain_edit_adds_no_undo_entry() -> None:
    sim = _fresh("dt")
    gain = _add_block(sim, "gain")
    history_len = len(sim._history)
    sim.handle_action("update_block_value", {"block_id": gain, "value": float("inf")})
    assert sim._error == "Gain value must be a finite number."
    assert len(sim._history) == history_len
    assert sim.blocks[gain]["value"] == 2.0


def test_successful_edit_is_one_undo_step() -> None:
    sim, ctf = _wired_dt_custom_tf()
    history_len = len(sim._history)
    sim.handle_action("update_block_value", {"block_id": ctf, "value": "z/(z-0.5)", "label": "G(z)"})
    assert len(sim._history) == history_len + 1
    assert sim.blocks[ctf]["label"] == "G(z)"
    sim.handle_action("undo", {})
    assert sim.blocks[ctf]["expression"] == "1"
    assert sim.blocks[ctf]["label"] == "H(z)"
    sim.handle_action("redo", {})
    assert sim.blocks[ctf]["expression"] == "z/(z-0.5)"
    assert sim.blocks[ctf]["label"] == "G(z)"


def test_rejected_cross_domain_block_adds_no_undo_entry() -> None:
    sim = _fresh("dt")
    _add_block(sim, "delay")
    sim.handle_action("undo", {})
    history_len = len(sim._history)
    assert len(sim._redo_history) == 1

    sim.handle_action("add_block", {"block_type": "integrator", "position": {"x": 0, "y": 0}})

    assert "not available in DT mode" in sim._error
    assert sim.get_state()["metadata"]["last_action_error"] == sim._error
    assert sim.blocks == {}
    assert len(sim._history) == history_len
    assert len(sim._redo_history) == 1


# ---------------------------------------------------------------------------
# Guard: a block in the wrong domain is reported, never computed or exported.
# No action reaches this state; it is forced here to exercise the guard.
# ---------------------------------------------------------------------------

def _force_domain(sim: BlockDiagramSimulator, system_type: str) -> None:
    sim.system_type = system_type
    sim.parameters["system_type"] = system_type
    sim._recompute_tf()


def test_delay_forced_into_ct_is_reported_not_read_as_integrator() -> None:
    sim = _fresh("dt")
    sim.handle_action("load_preset", {"preset": "first_order_dt"})
    _force_domain(sim, "ct")

    meta = sim.get_state()["metadata"]
    assert sim._tf_result is None
    assert meta["tf_error_kind"] == "domain"
    assert "Delay" in meta["tf_error"] and "continuous-time mode" in meta["tf_error"]
    assert meta["domain_error"] == meta["tf_error"]
    with pytest.raises(ExecutionError) as exc:
        sim.to_hub_data()
    assert exc.value.message.startswith("Cannot push to the hub: ")
    assert "Delay" in exc.value.message


def test_integrator_forced_into_dt_is_reported_not_read_as_delay() -> None:
    sim, _ = _ct_integrator_diagram()
    _force_domain(sim, "dt")

    meta = sim.get_state()["metadata"]
    assert sim._tf_result is None
    assert meta["tf_error_kind"] == "domain"
    assert "Integrator" in meta["tf_error"]
    assert meta["domain_error"] is not None
    with pytest.raises(ExecutionError):
        sim.to_hub_data()


def test_forced_stale_state_recovers_after_switching_back() -> None:
    sim, _ = _ct_integrator_diagram()
    _force_domain(sim, "dt")
    assert sim.get_state()["metadata"]["domain_error"] is not None
    _force_domain(sim, "ct")
    _assert_ct_integrator_tf(sim)
