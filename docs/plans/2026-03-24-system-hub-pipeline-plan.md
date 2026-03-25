# System Hub Pipeline — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect all 54 simulations through a reactive shared data hub with auto-read, manual push, multi-slot architecture, and a floating panel UI.

**Architecture:** Hybrid — frontend React Context + localStorage owns hub state (fast reads, offline-capable), backend provides stateless math validation/derivation endpoint (TF↔SS conversion, pole/zero extraction). Deep merge on push, stale controller detection, MIMO/SISO and CT/DT compatibility checks.

**Tech Stack:** React Context API, localStorage, KaTeX, scipy.signal (tf2ss, ss2tf, roots), scipy.linalg (solve_continuous_are), numpy

**Design Doc:** `docs/plans/2026-03-24-system-hub-pipeline-design.md`

**Security Note:** KaTeX rendering in HubPanel uses katex.renderToString which produces sanitized HTML output. The KaTeX library is already trusted and used throughout the codebase (RootLocusViewer, ControllerTuningLabViewer, etc). Follow the same pattern as existing viewers for rendering math content.

---

## Task 1: Backend Hub Validator — Pure Math Module

**Files:**
- Create: `backend/core/hub_validator.py`
- Test: `backend/tests/test_hub_validator.py`

**Step 1: Create test file with core validation tests**

```python
# backend/tests/test_hub_validator.py
import pytest
import numpy as np
from core.hub_validator import validate_and_enrich_control, validate_signal_slot, validate_circuit_slot


class TestControlSlotValidation:
    """Test TF→SS derivation, pole/zero extraction, property computation."""

    def test_first_order_tf(self):
        """G(s) = 1/(s+1): 1 pole at -1, stable, type 0."""
        data = {"source": "tf", "domain": "ct", "dimensions": {"n": 1, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [1.0, 1.0], "variable": "s"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        enriched = result["data"]
        assert enriched["order"] == 1
        assert enriched["system_type"] == 0
        assert enriched["stable"] == True
        assert len(enriched["poles"]) == 1
        assert abs(enriched["poles"][0]["real"] - (-1.0)) < 1e-10
        assert enriched["ss"] is not None
        assert enriched["controllable"] == True
        assert enriched["observable"] == True

    def test_second_order_underdamped(self):
        """G(s) = 1/(s^2+s+1): complex poles, stable."""
        data = {"source": "tf", "domain": "ct", "dimensions": {"n": 2, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [1.0, 1.0, 1.0], "variable": "s"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        enriched = result["data"]
        assert enriched["order"] == 2
        assert enriched["stable"] == True
        assert any(abs(p["imag"]) > 0.1 for p in enriched["poles"])

    def test_unstable_system(self):
        """G(s) = 1/(s-1): pole at +1, unstable."""
        data = {"source": "tf", "domain": "ct", "dimensions": {"n": 1, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [1.0, -1.0], "variable": "s"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        assert result["data"]["stable"] == False

    def test_type_1_system(self):
        """G(s) = 1/(s(s+1)): one pole at origin, type 1."""
        data = {"source": "tf", "domain": "ct", "dimensions": {"n": 2, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [1.0, 1.0, 0.0], "variable": "s"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        assert result["data"]["system_type"] == 1

    def test_type_2_system(self):
        """G(s) = 1/(s^2(s+1)): two poles at origin, type 2."""
        data = {"source": "tf", "domain": "ct", "dimensions": {"n": 3, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [1.0, 1.0, 0.0, 0.0], "variable": "s"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        assert result["data"]["system_type"] == 2

    def test_ss_to_tf_derivation(self):
        """Push SS matrices, should derive TF automatically."""
        data = {"source": "ss", "domain": "ct", "dimensions": {"n": 2, "m": 1, "p": 1},
                "ss": {"A": [[0, 1], [-2, -3]], "B": [[0], [1]], "C": [[1, 0]], "D": [[0]]}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        enriched = result["data"]
        assert enriched["tf"] is not None
        assert len(enriched["tf"]["num"]) > 0
        assert len(enriched["tf"]["den"]) > 0
        assert enriched["poles"] is not None

    def test_mimo_dimensions(self):
        """MIMO system: dimensions preserved, poles from eigenvalues."""
        data = {"source": "ss", "domain": "ct", "dimensions": {"n": 4, "m": 2, "p": 2},
                "ss": {"A": [[0,1,0,0],[0,0,1,0],[0,0,0,1],[-1,-2,-3,-4]],
                       "B": [[0,0],[0,0],[1,0],[0,1]],
                       "C": [[1,0,0,0],[0,0,1,0]],
                       "D": [[0,0],[0,0]]}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        enriched = result["data"]
        assert enriched["dimensions"]["m"] == 2
        assert enriched["dimensions"]["p"] == 2
        assert enriched["poles"] is not None

    def test_dt_system(self):
        """DT: H(z) = 1/(1 - 0.5z^-1), pole at 0.5, stable."""
        data = {"source": "tf", "domain": "dt", "dimensions": {"n": 1, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [1.0, -0.5], "variable": "z"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        enriched = result["data"]
        assert enriched["domain"] == "dt"
        assert enriched["stable"] == True

    def test_dt_unstable(self):
        """DT pole outside unit circle, unstable."""
        data = {"source": "tf", "domain": "dt", "dimensions": {"n": 1, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [1.0, -1.5], "variable": "z"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        assert result["data"]["stable"] == False

    def test_invalid_tf_empty_den(self):
        """Empty denominator should fail validation."""
        data = {"source": "tf", "domain": "ct", "dimensions": {"n": 0, "m": 1, "p": 1},
                "tf": {"num": [1.0], "den": [], "variable": "s"}}
        result = validate_and_enrich_control(data)
        assert result["success"] == False

    def test_zeros_extraction(self):
        """G(s) = (s+2)/(s^2+3s+1): one zero at -2."""
        data = {"source": "tf", "domain": "ct", "dimensions": {"n": 2, "m": 1, "p": 1},
                "tf": {"num": [1.0, 2.0], "den": [1.0, 3.0, 1.0], "variable": "s"}}
        result = validate_and_enrich_control(data)
        assert result["success"]
        zeros = result["data"]["zeros"]
        assert len(zeros) == 1
        assert abs(zeros[0]["real"] - (-2.0)) < 1e-10


class TestSignalSlotValidation:
    def test_valid_signal(self):
        data = {"signals": {"input": {"x": [0, 1, 2], "y": [0, 0.5, 1], "type": "ct", "label": "Step"}}}
        result = validate_signal_slot(data)
        assert result["success"]

    def test_empty_signals(self):
        data = {"signals": {}}
        result = validate_signal_slot(data)
        assert result["success"]


class TestCircuitSlotValidation:
    def test_valid_circuit(self):
        data = {"components": {"R": 1000, "C": 1e-6}, "topology": "rc_lowpass"}
        result = validate_circuit_slot(data)
        assert result["success"]
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_hub_validator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.hub_validator'`

**Step 3: Implement hub_validator.py**

```python
# backend/core/hub_validator.py
"""
Hub Validator - Stateless math module for enriching hub slot data.

Takes raw TF/SS data pushed to the hub, validates it, and derives
all related representations (TF to/from SS, poles, zeros, system properties).
No state stored. Pure function in, enriched data out.
"""

import numpy as np
from typing import Any, Dict, List, Optional
from scipy import signal as sig


def validate_and_enrich_control(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and enrich control system slot data.

    Given a source representation (TF or SS), derive all others:
    - TF to/from SS conversion
    - Pole/zero extraction
    - System type (number of integrators)
    - Stability check (CT: Re(p)<0, DT: |p|<1)
    - Controllability/observability (from SS)

    Args:
        data: Raw hub slot data with 'source', 'domain', 'tf' or 'ss'

    Returns:
        {success: bool, data: enriched_dict or None, error: str or None}
    """
    try:
        source = data.get("source", "tf")
        domain = data.get("domain", "ct")
        dims = data.get("dimensions", {"n": None, "m": 1, "p": 1})

        tf_data = data.get("tf")
        ss_data = data.get("ss")

        num, den = None, None
        A, B, C, D = None, None, None, None
        poles, zeros = [], []

        # --- Extract or derive TF and SS ---
        if source in ("tf", "poles_zeros") and tf_data:
            num = np.array(tf_data.get("num", []), dtype=float)
            den = np.array(tf_data.get("den", []), dtype=float)

            if len(den) == 0:
                return {"success": False, "data": None, "error": "Empty denominator"}
            if np.all(den == 0):
                return {"success": False, "data": None, "error": "All-zero denominator"}

            # Derive poles and zeros
            poles = _roots_to_list(np.roots(den))
            zeros = _roots_to_list(np.roots(num)) if len(num) > 1 else []

            # Derive SS from TF (SISO only)
            m = dims.get("m", 1)
            p = dims.get("p", 1)
            if m == 1 and p == 1 and len(den) > 1:
                try:
                    A_arr, B_arr, C_arr, D_arr = sig.tf2ss(num, den)
                    A = A_arr.tolist()
                    B = B_arr.tolist()
                    C = C_arr.tolist()
                    D = D_arr.tolist()
                    ss_data = {"A": A, "B": B, "C": C, "D": D}
                except Exception:
                    ss_data = None

        elif source == "ss" and ss_data:
            A = np.array(ss_data["A"], dtype=float)
            B = np.array(ss_data["B"], dtype=float)
            C = np.array(ss_data["C"], dtype=float)
            D = np.array(ss_data["D"], dtype=float)

            # Poles from eigenvalues of A
            eigenvalues = np.linalg.eigvals(A)
            poles = _roots_to_list(eigenvalues)

            # Derive TF from SS (SISO only)
            m = B.shape[1] if B.ndim == 2 else 1
            p_out = C.shape[0] if C.ndim == 2 else 1
            dims = {"n": A.shape[0], "m": int(m), "p": int(p_out)}

            if m == 1 and p_out == 1:
                try:
                    num_arr, den_arr = sig.ss2tf(A, B, C, D)
                    num = np.atleast_1d(num_arr.flatten())
                    den = np.atleast_1d(den_arr)
                    zeros = _roots_to_list(np.roots(num)) if len(num) > 1 else []
                    tf_data = {
                        "num": num.tolist(),
                        "den": den.tolist(),
                        "variable": data.get("tf", {}).get("variable", "s" if domain == "ct" else "z")
                    }
                except Exception:
                    tf_data = None
            else:
                # MIMO: skip TF derivation
                tf_data = data.get("tf")
                zeros = []

            ss_data = {"A": A.tolist(), "B": B.tolist(), "C": C.tolist(), "D": D.tolist()}

        elif source == "block_diagram":
            # Pass through block_diagram data, no enrichment
            enriched = {**data, "poles": [], "zeros": [], "system_type": None,
                        "order": None, "stable": None, "controllable": None, "observable": None}
            return {"success": True, "data": enriched, "error": None}
        else:
            return {"success": False, "data": None, "error": f"No valid TF or SS data for source='{source}'"}

        # --- Compute properties ---
        order = len(poles)
        if dims.get("n") is None:
            dims["n"] = order

        system_type = _compute_system_type(poles, domain)
        stable = _check_stability(poles, domain)

        controllable, observable = None, None
        if ss_data and A is not None:
            A_np = np.array(ss_data["A"], dtype=float) if not isinstance(A, np.ndarray) else A
            B_np = np.array(ss_data["B"], dtype=float) if not isinstance(B, np.ndarray) else B
            C_np = np.array(ss_data["C"], dtype=float) if not isinstance(C, np.ndarray) else C
            controllable = _check_controllability(A_np, B_np)
            observable = _check_observability(A_np, C_np)

        # --- Build enriched result ---
        enriched = {
            "source": source,
            "domain": domain,
            "dimensions": dims,
            "tf": {
                "num": num.tolist() if num is not None else (tf_data.get("num") if tf_data else None),
                "den": den.tolist() if den is not None else (tf_data.get("den") if tf_data else None),
                "variable": data.get("tf", {}).get("variable", "s" if domain == "ct" else "z"),
            } if (num is not None or tf_data) else None,
            "ss": ss_data,
            "poles": poles,
            "zeros": zeros,
            "system_type": system_type,
            "order": order,
            "stable": stable,
            "controllable": controllable,
            "observable": observable,
        }

        if "block_diagram" in data:
            enriched["block_diagram"] = data["block_diagram"]
        if "controller" in data:
            enriched["controller"] = data["controller"]

        return {"success": True, "data": enriched, "error": None}

    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def validate_signal_slot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate signal slot data. Lightweight type-check."""
    try:
        signals = data.get("signals", {})
        if not isinstance(signals, dict):
            return {"success": False, "data": None, "error": "signals must be a dict"}
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def validate_circuit_slot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate circuit slot data. Lightweight type-check."""
    try:
        components = data.get("components", {})
        if not isinstance(components, dict):
            return {"success": False, "data": None, "error": "components must be a dict"}
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def validate_optics_slot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate optics slot data."""
    try:
        elements = data.get("elements", [])
        if not isinstance(elements, list):
            return {"success": False, "data": None, "error": "elements must be a list"}
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


# --- Internal helpers ---

def _roots_to_list(roots: np.ndarray) -> List[Dict[str, float]]:
    """Convert numpy roots array to list of {real, imag} dicts."""
    return [{"real": float(np.real(r)), "imag": float(np.imag(r))} for r in roots]


def _compute_system_type(poles: List[Dict[str, float]], domain: str) -> int:
    """Count poles at origin (CT) or at z=1 (DT)."""
    count = 0
    tol = 1e-6
    for p in poles:
        if domain == "ct":
            if abs(p["real"]) < tol and abs(p["imag"]) < tol:
                count += 1
        else:
            if abs(p["real"] - 1.0) < tol and abs(p["imag"]) < tol:
                count += 1
    return count


def _check_stability(poles: List[Dict[str, float]], domain: str) -> bool:
    """CT: all Re(p) < 0. DT: all |p| < 1."""
    if not poles:
        return True
    for p in poles:
        if domain == "ct":
            if p["real"] >= 0:
                return False
        else:
            magnitude = (p["real"] ** 2 + p["imag"] ** 2) ** 0.5
            if magnitude >= 1.0:
                return False
    return True


def _check_controllability(A: np.ndarray, B: np.ndarray) -> bool:
    """Check controllability via rank of [B, AB, A^2B, ...]."""
    n = A.shape[0]
    ctrb = B.copy()
    Ak_B = B.copy()
    for _ in range(1, n):
        Ak_B = A @ Ak_B
        ctrb = np.hstack([ctrb, Ak_B])
    return int(np.linalg.matrix_rank(ctrb)) == n


def _check_observability(A: np.ndarray, C: np.ndarray) -> bool:
    """Check observability via rank of [C; CA; CA^2; ...]."""
    n = A.shape[0]
    obsv = C.copy()
    C_Ak = C.copy()
    for _ in range(1, n):
        C_Ak = C_Ak @ A
        obsv = np.vstack([obsv, C_Ak])
    return int(np.linalg.matrix_rank(obsv)) == n
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_hub_validator.py -v`
Expected: All 14 tests PASS

**Step 5: Commit**

```bash
git add backend/core/hub_validator.py backend/tests/test_hub_validator.py
git commit -m "feat(hub): add hub_validator math module with TF/SS derivation and tests"
```

---

## Task 2: Backend Hub API Endpoint

**Files:**
- Create: `backend/routes/__init__.py`
- Create: `backend/routes/hub.py`
- Modify: `backend/main.py:27-36` (add import), `backend/main.py:97-103` (mount router)

**Step 1: Create routes package and hub endpoint**

```bash
mkdir -p backend/routes
```

```python
# backend/routes/__init__.py
```

```python
# backend/routes/hub.py
"""Hub validation endpoint - stateless math enrichment for hub slot data."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, Optional

from core.hub_validator import (
    validate_and_enrich_control,
    validate_signal_slot,
    validate_circuit_slot,
    validate_optics_slot,
)

router = APIRouter(prefix="/api/hub", tags=["hub"])

SLOT_VALIDATORS = {
    "control": validate_and_enrich_control,
    "signal": validate_signal_slot,
    "circuit": validate_circuit_slot,
    "optics": validate_optics_slot,
}


class HubValidateRequest(BaseModel):
    slot: str
    data: Dict[str, Any]


class HubValidateResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/validate", response_model=HubValidateResponse)
async def validate_hub_data(request: HubValidateRequest):
    """Validate and enrich hub slot data. Stateless, no server-side storage."""
    validator = SLOT_VALIDATORS.get(request.slot)
    if not validator:
        return HubValidateResponse(success=False, error=f"Unknown slot: {request.slot}")

    result = validator(request.data)
    return HubValidateResponse(**result)
```

**Step 2: Mount router in main.py**

Add to `backend/main.py` imports (after line 36):
```python
from routes.hub import router as hub_router
```

Add after the app middleware setup (after line 116):
```python
# Mount hub validation router
app.include_router(hub_router)
```

**Step 3: Test endpoint manually**

Run: `cd backend && python -m uvicorn main:app --port 8000`

```bash
curl -X POST http://localhost:8000/api/hub/validate \
  -H "Content-Type: application/json" \
  -d '{"slot":"control","data":{"source":"tf","domain":"ct","dimensions":{"n":2,"m":1,"p":1},"tf":{"num":[1,2],"den":[1,3,1],"variable":"s"}}}'
```

Expected: JSON with `success: true`, enriched data including poles, zeros, SS matrices, stable: true

**Step 4: Commit**

```bash
git add backend/routes/__init__.py backend/routes/hub.py backend/main.py
git commit -m "feat(hub): add POST /api/hub/validate endpoint"
```

---

## Task 3: Frontend Hub Context + useHub Hook

**Files:**
- Create: `frontend/src/contexts/HubContext.jsx`
- Create: `frontend/src/hooks/useHub.js`

**Step 1: Create HubContext**

Create `frontend/src/contexts/HubContext.jsx` implementing:
- Multi-slot state (control, signal, circuit, optics)
- `pushToSlot(slot, data, simId)` that validates via `api.validateHubData()` and deep-merges
- `getSlot(slot)` for instant reads
- `subscribe(slot, callback)` for change notifications
- `clearSlot(slot)` and `clearAll()`
- localStorage persistence on every state change
- Cross-tab sync via `window.addEventListener('storage', ...)`
- Stale controller detection: when plant TF changes, mark existing controller as `stale: true`
- Deep merge utility: merges source into target without replacing top-level keys not in source

Key implementation details:
- Use `api.validateHubData(slotName, data)` from `../services/api` for backend enrichment (not raw fetch)
- If backend validation fails, store raw data as fallback (hub still works without backend)
- `pushToSlot` is async (awaits backend validation)
- `subscribe` returns an unsubscribe function
- Storage key: `'systemHub'`

**Step 2: Create useHub convenience hook**

Create `frontend/src/hooks/useHub.js` implementing:
- `useHub(slotName)` returns `{ slotData, pushToSlot, isHubAvailable, hubUpdated }`
- `slotData`: current data in the slot (null if empty)
- `pushToSlot(data, simId)`: convenience wrapper
- `isHubAvailable`: boolean, true if slot has data
- `hubUpdated`: counter that increments when slot changes after initial mount (for live update notifications)
- Subscribes to slot changes on mount, unsubscribes on unmount

**Step 3: Commit**

```bash
git add frontend/src/contexts/HubContext.jsx frontend/src/hooks/useHub.js
git commit -m "feat(hub): add HubContext provider and useHub hook with localStorage persistence"
```

---

## Task 4: Frontend Hub API Client Method

**Files:**
- Modify: `frontend/src/services/api.js:263-275`

**Step 1: Add validateHubData method to ApiClient**

Add before the closing `}` of the ApiClient class (before line 268):

```javascript
  /**
   * Validate and enrich hub slot data via backend
   * @param {string} slot - Slot name (control, signal, circuit, optics)
   * @param {Object} data - Slot data to validate
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   */
  async validateHubData(slot, data) {
    try {
      const response = await apiClient.post('/hub/validate', { slot, data });
      return {
        success: response.data.success,
        data: response.data.data || null,
        error: response.data.error || null,
      };
    } catch (error) {
      return handleError(error);
    }
  }
```

**Step 2: Commit**

```bash
git add frontend/src/services/api.js
git commit -m "feat(hub): add validateHubData API method"
```

---

## Task 5: Hub UI Components + CSS

**Files:**
- Create: `frontend/src/components/HubButton.jsx`
- Create: `frontend/src/components/HubPanel.jsx`
- Create: `frontend/src/styles/Hub.css`

**Step 1: Create HubButton**

Small component: SVG hub icon, `isOpen`/`onToggle` props, green badge dot when any slot has data. Uses `useHubContext()` to check `hubState`.

**Step 2: Create HubPanel**

Floating panel component with:
- Slot tabs (Control, Signal, Circuit, Optics) with activity dots
- Per-slot views:
  - **ControlSlotView**: Source info, domain, dimensions, TF (KaTeX via `katex.renderToString` — same trusted pattern used in RootLocusViewer and other existing viewers), SS matrices (KaTeX), properties (order, type, stable/controllable/observable badges), poles/zeros chips, controller layer with stale badge
  - **SignalSlotView**: Signal list with sample counts
  - **CircuitSlotView**: Topology + component values
  - **OpticsSlotView**: Element list
- Footer: Clear Slot, Export JSON buttons
- Backdrop overlay, close button, slide-in animation

KaTeX rendering follows the identical pattern already used throughout the codebase (e.g., `RootLocusViewer.jsx`, `ControllerTuningLabViewer.jsx`, `SteadyStateErrorViewer.jsx`).

**Step 3: Create Hub.css**

~300 lines. Key classes and specifications:

| Class | Purpose | Key styles |
|-------|---------|------------|
| `.hub-button` | Nav button | 36x36px, `var(--border-color)` border, `var(--radius-md)`, hover: `var(--primary-light)` bg |
| `.hub-button--open` | Active state | `var(--primary-color)` border, `var(--primary-light)` bg |
| `.hub-button__badge` | Activity dot | 8x8px, absolute top-right, `var(--success-color)` bg, `var(--radius-full)` |
| `.hub-backdrop` | Overlay | fixed, full viewport, `rgba(0,0,0,0.4)`, z-index 998 |
| `.hub-panel` | Side panel | fixed right, 380px wide, 100vh, `var(--surface-color)` bg, z-index 999, slide-in via `transform` |
| `.hub-panel__header` | Title bar | flex, `var(--text-primary)`, border-bottom `var(--border-color)` |
| `.hub-panel__tabs` | Slot tabs | flex row, gap 4px, `var(--background-secondary)` bg, `var(--radius-sm)` |
| `.hub-tab--active` | Active tab | `var(--primary-color)` bg, white text |
| `.hub-tab__dot` | Tab dot | 6x6px inline, `var(--primary-color)` bg |
| `.hub-slot__section` | Content section | border-bottom, padding 12px |
| `.hub-slot__section--stale` | Stale controller | `var(--warning-color)` left border |
| `.hub-prop__badge--success` | Green badge | `var(--success-color)` bg |
| `.hub-prop__badge--danger` | Red badge | `var(--error-color)` bg |
| `.hub-stale-badge` | Stale label | `var(--warning-color)` bg, small text |
| `.hub-pole` | Pole chip | inline, monospace, `var(--background-secondary)` bg, `var(--radius-sm)` |
| `.hub-action` | Footer button | `var(--border-color)` border, hover glow |
| `.hub-action--danger` | Clear button | `var(--error-color)` text on hover |
| `.hub-toast` | Update toast | fixed bottom-right, `var(--surface-color)` bg, `var(--primary-color)` left border, slide-up animation |

Include `[data-theme="light"]` overrides for panel bg, text colors, borders.

**Step 4: Commit**

```bash
git add frontend/src/components/HubButton.jsx frontend/src/components/HubPanel.jsx frontend/src/styles/Hub.css
git commit -m "feat(hub): add HubButton, HubPanel UI components with CSS"
```

---

## Task 6: Wire Hub into App.jsx

**Files:**
- Modify: `frontend/src/App.jsx:7-14` (imports), `frontend/src/App.jsx:62-100` (JSX)

**Step 1: Add imports**

After line 14, add:
```javascript
import { HubProvider } from './contexts/HubContext'
import HubButton from './components/HubButton'
import HubPanel from './components/HubPanel'
```

**Step 2: Add hub state**

In App function, after line 28, add:
```javascript
const [hubOpen, setHubOpen] = useState(false);
const toggleHub = useCallback(() => setHubOpen(prev => !prev), []);
```

**Step 3: Wrap in HubProvider**

Wrap the entire return JSX `<div className="app">...</div>` in `<HubProvider>...</HubProvider>`.

**Step 4: Add HubButton to header toolbar**

In `<div className="header-toolbar">` (line 79), add before `<ThemeToggle />`:
```jsx
<HubButton isOpen={hubOpen} onToggle={toggleHub} />
```

**Step 5: Add HubPanel**

After `<KeyboardShortcutsModal />` (line 116), add:
```jsx
<HubPanel isOpen={hubOpen} onClose={() => setHubOpen(false)} />
```

**Step 6: Verify**

Run: `cd frontend && npm run dev`
Check: Hub button appears in nav bar, clicking opens empty panel with 4 tabs.

**Step 7: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat(hub): wire HubProvider, HubButton, HubPanel into App layout"
```

---

## Task 7: Backend BaseSimulator Hub Interface

**Files:**
- Modify: `backend/simulations/base_simulator.py:24-27` (class attrs), after line 168 (new methods)

**Step 1: Add hub class attributes**

After `DEFAULT_PARAMS` (line 26), add:
```python
    HUB_SLOTS: List[str] = []
    HUB_DOMAIN: str = "ct"
    HUB_DIMENSIONS: Dict[str, Any] = {"n": None, "m": 1, "p": 1}
```

**Step 2: Add default to_hub_data and from_hub_data methods**

After `get_default_params()` (line 168), add:

- `to_hub_data()`: Scans `self.parameters` for common TF key patterns (`numerator`, `num_coeffs`, `custom_num`, `plant_num`, `tf_numerator` and corresponding den keys). Parses comma-separated strings to float lists. Returns hub slot data dict or None.
- `from_hub_data(hub_data)`: Checks SISO/MIMO and CT/DT compatibility. Injects hub TF num/den as comma-separated strings into matching parameter keys. Returns bool.
- `_parse_coeffs(val)`: Static helper to parse `"1, 3, 2"` to `[1.0, 3.0, 2.0]`.

**Step 3: Add hub info to get_state metadata**

Modify base `get_state()` to add `hub_slots`, `hub_domain`, `hub_dimensions` to metadata when `HUB_SLOTS` is non-empty. Note: most sims override `get_state()`, so the metadata addition also needs to happen in each sim's override. The base implementation serves as documentation.

**Step 4: Commit**

```bash
git add backend/simulations/base_simulator.py
git commit -m "feat(hub): add hub interface to BaseSimulator with default TF adapters"
```

---

## Task 8: Add HUB_SLOTS to All 54 Backend Simulators

**Files:**
- Modify: All 54 `backend/simulations/*.py` files

This is the largest task. For each simulator:

1. Add `HUB_SLOTS`, `HUB_DOMAIN`, `HUB_DIMENSIONS` class attributes
2. Add `hub_slots`, `hub_domain`, `hub_dimensions` to the metadata dict in `get_state()`
3. For ~15 sims with non-standard parameter names, override `to_hub_data()` and `from_hub_data()`

**Detailed per-sim mapping:**

### CT SISO sims (default adapter works): ~25 sims
Add `HUB_SLOTS = ['control']` and `HUB_DOMAIN = "ct"` only.

### DT sims: ~6 sims
Add `HUB_SLOTS = ['control']` and `HUB_DOMAIN = "dt"`.

### Custom adapter sims: ~15 sims

| Sim | Override reason |
|-----|----------------|
| `routh_hurwitz.py` | Uses `poly_coeffs` (den only), num is always [1] |
| `second_order_system.py` | Uses `omega_0`, `Q_slider`, compute TF from params |
| `controller_tuning_lab.py` | Preset-based, needs to extract current computed TF |
| `lead_lag_designer.py` | Preset-based, needs to extract current computed TF |
| `block_diagram_builder.py` | Source-only, exports block topology + computed TF |
| `signal_flow_scope.py` | Reads block_diagram from hub, exports per-node TF |
| `mimo_design_studio.py` | Uses `matrix_a/b/c/d`, MIMO dimensions |
| `state_space_analyzer.py` | Uses `tf_numerator`/`tf_denominator` or `matrix_a/b/c/d` |
| `nonlinear_control_lab.py` | Exports linearized SS + controller |
| `dc_motor.py` | Parametric (R, L, K, J, B), compute TF |
| `mass_spring_system.py` | Parametric (m, c, k), compute TF |
| `furuta_pendulum.py` | Complex SS from pendulum params |
| `laplace_roc.py` | Uses `custom_num_coeffs`/`custom_den_coeffs` + pole sliders |
| `phase_portrait.py` | SS-based, custom ODEs |
| `rc_lowpass_filter.py` | Dual-slot (circuit + control), compute TF from R,C |

### Signal slot sims: ~6 sims
`to_hub_data()` extracts output signal arrays from computed plot data.

### Circuit slot: 3 sims
`to_hub_data()` returns component values and topology.

### Optics: 1 sim
`to_hub_data()` returns lens elements.

**Commit in batches by category:**

```bash
git add backend/simulations/*.py
git commit -m "feat(hub): add HUB_SLOTS and hub adapters to all 54 simulators"
```

---

## Task 9: Hub-Aware useSimulation Hook

**Files:**
- Modify: `frontend/src/hooks/useSimulation.js`

**Step 1: Add hub auto-read after initial state load**

After the simulation state loads successfully (inside the `if (stateResult.success)` block around line 570):

1. Read `hub_slots` and `hub_domain` from `stateResult.metadata`
2. If hub has data in a matching slot, check compatibility (SISO/MIMO, CT/DT)
3. Map hub TF to sim's parameter names using the sim's `controls` definitions
4. Call `api.updateParameters(simId, hubParams)` to inject hub data
5. Update plots, params, metadata from the result

Key details:
- Use `useHubContext()` wrapped in try/catch (graceful if HubProvider not mounted)
- Only apply hub data on initial mount, not on every re-render
- Match param names by scanning controls for common TF key patterns: `numerator`, `num_coeffs`, `custom_num`, `plant_num`, `tf_numerator` (and den equivalents)

**Step 2: Add hub info to returned object**

Add `hubSlots` and `hubDomain` to the returned hook object.

**Step 3: Commit**

```bash
git add frontend/src/hooks/useSimulation.js
git commit -m "feat(hub): add hub auto-read to useSimulation hook"
```

---

## Task 10: Push to Hub Button + to_hub_data Action

**Files:**
- Modify: `frontend/src/components/SimulationViewer.jsx`
- Modify: `backend/main.py` (execute endpoint action handler)

**Step 1: Add Push to Hub button in SimulationViewer**

Import `useHub` hook. Determine primary slot from `metadata?.hub_slots?.[0]`. Add a "Push to Hub" button near the control panel that:
1. Calls `api.executeSimulation(simId, 'to_hub_data', {})`
2. If successful, calls `pushToSlot(result.data.hub_data, simId)`

Also add a "Synced from Hub" indicator when `isHubAvailable && primarySlot`.

**Step 2: Add `to_hub_data` action in backend**

In `backend/main.py`, in the execute endpoint's action handling, add a case for `action == "to_hub_data"` that calls `simulator.to_hub_data()` and returns the result.

**Step 3: Commit**

```bash
git add frontend/src/components/SimulationViewer.jsx backend/main.py
git commit -m "feat(hub): add Push to Hub button and to_hub_data action"
```

---

## Task 11: Hub Live Update Toast

**Files:**
- Modify: `frontend/src/components/SimulationViewer.jsx`
- Modify: `frontend/src/styles/Hub.css`

**Step 1: Add toast notification**

Use `hubUpdated` counter from `useHub`. When it increments (and is > 0), show a toast with "Hub updated" + Reload/Dismiss buttons. Auto-dismiss after 8 seconds.

Reload button refreshes the page (simple approach for v1). Dismiss hides the toast.

**Step 2: Add toast CSS to Hub.css**

**Step 3: Commit**

```bash
git add frontend/src/components/SimulationViewer.jsx frontend/src/styles/Hub.css
git commit -m "feat(hub): add live update toast notification"
```

---

## Task 12: End-to-End Testing

**Step 1: Start backend and frontend**

```bash
cd backend && python -m uvicorn main:app --reload --port 8000 &
cd frontend && npm run dev &
```

**Step 2: Test hub validation endpoint**

```bash
curl -X POST http://localhost:8000/api/hub/validate \
  -H "Content-Type: application/json" \
  -d '{"slot":"control","data":{"source":"tf","domain":"ct","dimensions":{"n":2,"m":1,"p":1},"tf":{"num":[1,2],"den":[1,3,1],"variable":"s"}}}'
```

Expected: enriched response with poles, zeros, SS, stability

**Step 3: Browser integration tests**

1. Open Block Diagram Builder, build system, Push to Hub
2. Open Hub panel, verify control slot shows TF + SS + properties
3. Navigate to Root Locus, verify auto-loads hub plant
4. Navigate to Nyquist-Bode, verify auto-loads
5. Go to Controller Tuning Lab, verify auto-loads, design PID, push controller
6. Open Hub panel, verify controller layer
7. Change plant in BDB, push, verify controller shows "stale"

**Step 4: Edge case tests**

- MIMO from MIMO Design Studio: SISO sims skip auto-read
- DT from Z-Transform ROC: CT sims skip auto-read
- Clear hub slot: sims work standalone
- Two tabs: push in one, verify storage event syncs to other

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat(hub): end-to-end system hub pipeline connecting 54 simulations"
```

---

## Task Summary

| Task | Description | New Files | Modified Files |
|------|-------------|-----------|----------------|
| 1 | Hub validator math module | 2 | 0 |
| 2 | Hub API endpoint | 2 | 1 |
| 3 | HubContext + useHub hook | 2 | 0 |
| 4 | API client method | 0 | 1 |
| 5 | HubButton + HubPanel + CSS | 3 | 0 |
| 6 | Wire into App.jsx | 0 | 1 |
| 7 | BaseSimulator hub interface | 0 | 1 |
| 8 | HUB_SLOTS on all 54 sims | 0 | 54 |
| 9 | Hub-aware useSimulation | 0 | 1 |
| 10 | Push to Hub button | 0 | 2 |
| 11 | Live update toast | 0 | 2 |
| 12 | End-to-end testing | 0 | 0 |
| **Total** | | **9 new** | **~64 modified** |
