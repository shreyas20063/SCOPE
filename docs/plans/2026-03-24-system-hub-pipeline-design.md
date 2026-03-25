# System Hub Pipeline — Design Document

**Date**: 2026-03-24
**Status**: Approved
**Scope**: Connect all 54 simulations through a reactive shared data hub

---

## 1. Overview

A centralized **System Hub** that acts as a shared data layer across all 54 simulations. Any simulation can push its current system definition to the hub, and all other simulations auto-read from it. The hub is visible as a collapsible floating panel accessible from a top-right button on every page.

### Core Principles

- **Auto-read, manual push**: Sims automatically load hub data on mount. Writing back requires explicit "Push to Hub" action.
- **Multi-slot**: 4 independent data slots (Control, Signal, Circuit, Optics) so different domains don't interfere.
- **Hybrid architecture**: Frontend owns state (React Context + localStorage). Backend provides math-only validation/derivation (TF↔SS conversion, pole/zero extraction).
- **Deep merge on push**: Pushing controller data doesn't overwrite plant data — fields merge into the slot.
- **Graceful degradation**: Hub is purely additive. Every sim works standalone if the hub is empty or unavailable.

---

## 2. Hub Data Model

### 2.1 Control System Slot

```json
{
  "source": "tf | ss | block_diagram | poles_zeros",
  "domain": "ct | dt",
  "dimensions": { "n": 2, "m": 1, "p": 1 },

  "tf": { "num": [1, 2], "den": [1, 3, 1], "variable": "s | z" },
  "ss": { "A": [[]], "B": [[]], "C": [[]], "D": [[]], "n": 2, "m": 1, "p": 1 },

  "poles": [{"real": -1.5, "imag": 0.866}],
  "zeros": [{"real": -2, "imag": 0}],
  "system_type": 1,
  "order": 2,
  "stable": true,
  "controllable": true,
  "observable": true,

  "block_diagram": { "blocks": {}, "connections": [] },

  "controller": {
    "type": "pid | lead_lag | state_feedback | lqr | lqg",
    "params": {},
    "cl_tf": { "num": [], "den": [] },
    "cl_poles": [],
    "cl_stable": true,
    "stale": false,
    "designed_for": { "tf": { "num": [], "den": [] } }
  },

  "_meta": {
    "pushed_by": "root_locus",
    "timestamp": 1711270400000
  }
}
```

### 2.2 Signal Slot

```json
{
  "signals": {
    "input": { "x": [], "y": [], "type": "ct | dt", "label": "Input" },
    "output": { "x": [], "y": [], "type": "ct | dt", "label": "Output" }
  },
  "sample_rate": 1000,
  "duration": 1.0,
  "_meta": { "pushed_by": "signal_operations", "timestamp": 0 }
}
```

### 2.3 Circuit Slot

```json
{
  "components": { "R": 1000, "C": 0.0001, "L": null },
  "topology": "rc_lowpass | rlc_series | ...",
  "tf": { "num": [], "den": [] },
  "_meta": { "pushed_by": "rc_lowpass_filter", "timestamp": 0 }
}
```

### 2.4 Optics Slot

```json
{
  "elements": [{ "type": "lens", "f": 50, "position": 100 }],
  "wavelength": 550,
  "_meta": { "pushed_by": "lens_optics", "timestamp": 0 }
}
```

---

## 3. Compatibility Rules

### 3.1 MIMO↔SISO

When auto-reading from the control slot, sims check `dimensions`:
- SISO sims (`m=1, p=1` required): skip auto-read if dimensions are MIMO. Show info: "Hub system is MIMO — not applicable."
- MIMO sims: accept any dimensions.

### 3.2 CT↔DT Domain

Sims declare their domain. Auto-read checks `domain` field:
- CT-only sims skip DT hub data (and vice versa).
- Domain-agnostic sims (e.g., `ct_dt_comparator`) accept either.

### 3.3 Stale Controller Detection

When plant data (tf/ss/poles) changes in the hub:
1. If a controller layer exists, set `controller.stale = true`
2. Store `controller.designed_for = { tf: <previous_tf> }`
3. Hub panel shows warning badge on controller section
4. Sims reading controller data see the stale flag and can warn the user

---

## 4. Sync Mechanism

### 4.1 Push Flow (sim → hub)

```
User clicks "Push to Hub" in sim
  → Sim calls to_hub_data() to serialize its state
  → HubProvider.pushToSlot(slotName, data, simId)
    → POST /api/hub/validate { slot, data }
    → Backend derives: SS from TF (or TF from SS), poles, zeros,
      system_type, stability, controllability, observability
    → Returns enriched data
    → If backend fails: store raw data without enrichment (fallback)
  → Deep merge enriched data into hub slot (don't replace)
  → Update localStorage
  → Notify all subscribers
```

### 4.2 Auto-Read on Mount (hub → sim)

```
Sim component mounts
  → useHub(slotName) returns current slot data
  → Check compatibility (SISO/MIMO, CT/DT)
  → If compatible: call from_hub_data() to inject into sim parameters
  → Trigger parameter update via existing useSimulation hook
  → Show "Synced from Hub" indicator
```

### 4.3 Live Sync While Interacting

```
Hub updates while sim is already open and loaded
  → Do NOT auto-overwrite (protects in-progress work)
  → Show non-intrusive toast: "Hub updated — [Reload]"
  → User clicks Reload → re-runs from_hub_data() with new data
  → Toast auto-dismisses after 8 seconds if ignored
```

### 4.4 Deep Merge Rules

| Push contains | Effect on slot |
|---------------|---------------|
| `tf` or `ss` (plant data) | Replace plant fields, re-derive, mark controller stale |
| `controller` only | Merge controller into slot, plant untouched |
| `block_diagram` only | Merge topology, plant untouched |
| Full slot object | Replace entire slot |

---

## 5. UI Design

### 5.1 Hub Button (top-right nav)

- Persistent button on every page, positioned in the navigation bar
- Icon: hub/network glyph
- Badge dot when hub has data (color-coded by slot activity)
- Click toggles the floating panel

### 5.2 Floating Hub Panel

- Slides in from right edge as overlay (does not push page content)
- Fixed width ~380px, full viewport height
- Semi-transparent backdrop, click outside to close
- Stays open across route navigation (persists in React state)

**Panel structure:**
```
┌─────────────────────────────────┐
│  System Hub              [✕]    │
│─────────────────────────────────│
│  [Control] [Signal] [Circuit] [Optics]  ← slot tabs
│─────────────────────────────────│
│  Source: Block Diagram Builder  │
│  Domain: Continuous-time        │
│  Last updated: 2s ago           │
│                                 │
│  Transfer Function              │
│  G(s) = (s+2)/(s²+3s+1)       │  ← KaTeX
│                                 │
│  State Space                    │
│  A = [0  1; -1  -3]  B = [0;1]│  ← KaTeX
│  C = [1  0]  D = [0]           │
│                                 │
│  Properties                     │
│  Order: 2 │ Type: 0 │ Stable ✓ │
│  Controllable ✓ │ Observable ✓  │
│  Poles: -1.5 ± 0.87j           │
│                                 │
│  Controller  ⚠ stale            │
│  PID: Kp=2.1 Ki=0.5 Kd=0.3    │
│  CL Stable ✓                   │
│                                 │
│  ─── Connected Sims ───         │
│  ✓ Root Locus (synced)          │
│  ✓ Bode (synced)               │
│  ○ Nyquist (not visited)        │
│                                 │
│  [Clear Slot]  [Export JSON]    │
└─────────────────────────────────┘
```

### 5.3 Per-Simulation Hub Controls

On each simulation page, near the control panel:
- **"Push to Hub"** button — visible when sim has data to push
- **"Synced from Hub"** indicator — shown when sim loaded hub data on mount
- **"Hub Updated — Reload"** toast — shown when hub changes while sim is active

Push button is contextual: only shows slots relevant to that sim (based on `HUB_SLOTS`).

---

## 6. Slot Mapping — All 54 Simulations

### 6.1 Control System Slot

**Plant definers (push plant TF/SS/topology):**

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| block_diagram_builder | — | block_diagram, TF (overall) |
| signal_flow_scope | block_diagram | TF (per-node) |
| state_space_analyzer | SS | SS matrices |
| mimo_design_studio | SS | SS + controller (K, L) |
| nonlinear_control_lab | SS | linearized SS + controller |
| dc_motor | — | plant TF |
| furuta_pendulum | — | plant SS |
| mass_spring_system | — | plant TF |
| second_order_system | — | plant TF |
| rc_lowpass_filter | — | circuit TF |

**Stability analysis (read plant, push analysis results):**

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| root_locus | TF | gain K, CL poles |
| routh_hurwitz | TF | stability verdict |
| nyquist_stability | TF | GM, PM, stability |
| nyquist_bode_comparison | TF | margins |
| steady_state_error | TF | system type, error constants |
| complex_poles_modes | poles | mode shapes |
| pole_behavior | TF | pole trajectories |
| resonance_anatomy | TF | resonance freq |
| delay_instability | TF | delay margin |
| ct_dt_poles | poles | CT↔DT mapping |

**Controller design (read plant, push controller):**

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| controller_tuning_lab | TF | controller (PID/LQR/LQG) + CL TF |
| lead_lag_designer | TF | compensator TF + CL TF |

**Transform domain (read TF/signals):**

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| laplace_roc | TF | ROC region |
| laplace_properties | TF | transform properties |
| z_transform_roc | TF (DT) | z-domain ROC |
| z_transform_properties | TF (DT) | z-domain properties |
| inverse_z_transform | TF (DT) | time-domain sequence |
| fourier_series | — | Fourier coefficients |
| fourier_phase_vs_magnitude | — | spectrum |
| ode_laplace_solver | TF | ODE solution |
| ivt_fvt_visualizer | TF | initial/final values |
| eigenfunction_tester | TF | eigenvalue response |
| vector_freq_response | TF | frequency response |

**Signal processing (read TF for filtering, or standalone):**

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| ct_impulse_response | TF | response signals |
| convolution_simulator | signals | convolved output |
| signal_operations | — | signals |
| sampling_reconstruction | signals | sampled signals |
| aliasing_quantization | signals | aliased signals |
| modulation_techniques | signals | modulated signals |
| impulse_construction | — | impulse signals |
| dt_difference_equation | TF (DT) | DT response |
| dt_system_representations | TF (DT) | DT system forms |
| dt_ct_comparator | TF | CT vs DT comparison |
| cascade_parallel | TF | decomposed TFs |
| polynomial_multiplication | TF | product TF |
| operator_algebra | TF | operator form |
| fundamental_modes | TF | mode decomposition |
| audio_freq_response | TF | filtered audio |
| feedback_convergence | TF | convergence data |
| cyclic_path_detector | block_diagram | cycles |
| phase_portrait | SS | phase plane |

### 6.2 Signal Slot

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| signal_operations | signals | transformed signals |
| convolution_simulator | signals | result signal |
| sampling_reconstruction | signals | sampled/reconstructed |
| aliasing_quantization | signals | aliased signal |
| modulation_techniques | signals | modulated signal |
| impulse_construction | — | impulse signal |
| ct_impulse_response | — | response signals |
| audio_freq_response | — | audio signal |

### 6.3 Circuit Slot

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| rc_lowpass_filter | components | TF + component values |
| amplifier_topologies | components | gain, impedance |
| feedback_system_analysis | topology | loop gain TF |

### 6.4 Optics Slot

| Sim ID | Reads | Pushes |
|--------|-------|--------|
| lens_optics | elements | lens config |

---

## 7. Architecture — New & Modified Files

### 7.1 New Files

| File | Purpose | ~Lines |
|------|---------|--------|
| `backend/core/hub_validator.py` | TF↔SS conversion, pole/zero extraction, system properties. Stateless math. | ~350 |
| `backend/routes/hub.py` | `POST /api/hub/validate` endpoint | ~80 |
| `frontend/src/contexts/HubContext.jsx` | React Context + Provider. State, push/pull, localStorage, cross-tab sync via `storage` event | ~250 |
| `frontend/src/hooks/useHub.js` | Convenience hook: `useHub('control')` returns slot data + push fn + status | ~60 |
| `frontend/src/components/HubPanel.jsx` | Floating panel UI. Slot tabs, KaTeX, connected sims, clear/export | ~400 |
| `frontend/src/components/HubButton.jsx` | Top-right nav button. Toggle panel, badge for active slots | ~50 |
| `frontend/src/styles/Hub.css` | Panel overlay, glass effect, slot tabs, animations | ~300 |

### 7.2 Modified Files

| File | Change |
|------|--------|
| `backend/main.py` | Mount hub router |
| `backend/simulations/base_simulator.py` | Add `HUB_SLOTS`, default `from_hub_data()`, default `to_hub_data()` |
| `frontend/src/App.jsx` | Wrap in `<HubProvider>`, add `<HubButton>` + `<HubPanel>` |
| `frontend/src/components/SimulationViewer.jsx` | Add Push to Hub button, pass hub data to viewers |
| `frontend/src/hooks/useSimulation.js` | Hub-awareness: auto-inject hub data when slot matches |
| `frontend/src/styles/App.css` | Hub button positioning in nav bar |
| All 54 backend simulators | Add `HUB_SLOTS` + override `from_hub_data()`/`to_hub_data()` where needed |
| All ~15 custom frontend viewers | Integrate `useHub()` for auto-read + Push button |

### 7.3 Adapter Boilerplate Reduction

`BaseSimulator` provides default implementations for the ~35 sims that follow the standard TF pattern:

```python
class BaseSimulator:
    HUB_SLOTS = []
    HUB_DOMAIN = "ct"  # or "dt", overridden per sim
    HUB_DIMENSIONS = {"n": None, "m": 1, "p": 1}  # SISO default

    def from_hub_data(self, hub_data):
        """Default: load TF num/den into standard parameter names."""
        if 'tf' in hub_data and hub_data['tf']:
            for key in ('numerator', 'num_coeffs', 'num'):
                if key in self.PARAMETER_SCHEMA:
                    self.parameters[key] = hub_data['tf']['num']
                    break
            for key in ('denominator', 'den_coeffs', 'den'):
                if key in self.PARAMETER_SCHEMA:
                    self.parameters[key] = hub_data['tf']['den']
                    break

    def to_hub_data(self):
        """Default: export TF from standard parameter names."""
        num = den = None
        for key in ('numerator', 'num_coeffs', 'num'):
            if key in self.parameters:
                num = self.parameters[key]; break
        for key in ('denominator', 'den_coeffs', 'den'):
            if key in self.parameters:
                den = self.parameters[key]; break
        if num is not None and den is not None:
            return {'source': 'tf', 'domain': self.HUB_DOMAIN,
                    'dimensions': self.HUB_DIMENSIONS,
                    'tf': {'num': num, 'den': den,
                           'variable': 'z' if self.HUB_DOMAIN == 'dt' else 's'}}
        return None
```

Only ~15 sims with non-standard parameter schemas need custom overrides.

---

## 8. Backend Validation Endpoint

### `POST /api/hub/validate`

**Request:**
```json
{
  "slot": "control",
  "data": {
    "source": "tf",
    "domain": "ct",
    "dimensions": { "n": 2, "m": 1, "p": 1 },
    "tf": { "num": [1, 2], "den": [1, 3, 1], "variable": "s" }
  }
}
```

**Response (success):**
```json
{
  "success": true,
  "data": {
    "source": "tf",
    "domain": "ct",
    "dimensions": { "n": 2, "m": 1, "p": 1 },
    "tf": { "num": [1, 2], "den": [1, 3, 1], "variable": "s" },
    "ss": { "A": [[0,1],[-1,-3]], "B": [[0],[1]], "C": [[2,1]], "D": [[0]] },
    "poles": [{"real": -1.5, "imag": 0.866}, {"real": -1.5, "imag": -0.866}],
    "zeros": [{"real": -2, "imag": 0}],
    "system_type": 0,
    "order": 2,
    "stable": true,
    "controllable": true,
    "observable": true
  }
}
```

**Response (failure):**
```json
{
  "success": false,
  "error": "Cannot compute TF — disconnected block diagram",
  "data": null
}
```

**Derivation logic** (`hub_validator.py`):
- If source is TF → derive SS via `scipy.signal.tf2ss`, compute poles via `np.roots(den)`, zeros via `np.roots(num)`, system_type by counting poles at origin, stability by checking Re(poles) < 0, controllability/observability from SS
- If source is SS → derive TF via `scipy.signal.ss2tf`, then same as above
- If source is block_diagram → compute overall TF via Mason's gain formula (reuse existing `signal_flow_scope` logic), then derive all
- Circuit and optics slots: pass through with minimal validation (type checking)

---

## 9. Build Sequence

```
Phase 1: Core Infrastructure
  1. backend/core/hub_validator.py — pure math, testable standalone
  2. backend/routes/hub.py — validation endpoint + mount in main.py
  3. frontend/src/contexts/HubContext.jsx — React Context + localStorage
  4. frontend/src/hooks/useHub.js — convenience hook

Phase 2: UI
  5. frontend/src/components/HubPanel.jsx — floating panel
  6. frontend/src/components/HubButton.jsx — nav button
  7. frontend/src/styles/Hub.css — styling
  8. Wire into App.jsx — HubProvider wrapper + HubButton + HubPanel

Phase 3: Integration Layer
  9. backend/simulations/base_simulator.py — default hub methods
  10. frontend/src/hooks/useSimulation.js — hub-awareness
  11. frontend/src/components/SimulationViewer.jsx — Push button + hub indicator

Phase 4: Per-Simulation Wiring (54 sims)
  12. Add HUB_SLOTS + HUB_DOMAIN to all 54 backend simulators
  13. Custom from_hub_data/to_hub_data for ~15 non-standard sims
  14. Wire useHub into all ~15 custom frontend viewers
  15. Test each sim's push/pull cycle

Phase 5: Polish
  16. Cross-tab sync via storage event listener
  17. Toast notifications for live hub updates
  18. Export/import hub state as JSON
  19. End-to-end testing: BDB → Root Locus → Controller Lab → Bode pipeline
```

---

## 10. Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| MIMO data in SISO sim | Check `dimensions` before auto-read, show info message |
| CT/DT domain mismatch | Check `domain` before auto-read, skip incompatible |
| Live sync overwrites active work | Auto-read on mount only; toast notification while interacting |
| Push replaces entire slot | Deep merge — controller push doesn't overwrite plant |
| Stale controller after plant change | `stale` flag + `designed_for` reference + warning badge |
| Backend down during push | Store raw data without enrichment, re-validate later |
| Empty hub / first use | `useHub` returns null, auto-read is a no-op |
| localStorage full | Hub data is small (~5-20KB per slot). Not a practical concern |
| Browser clears storage | Graceful fallback to standalone mode |
| Circular push→read loop | Push is manual, merge is field-level — no circular trigger |
