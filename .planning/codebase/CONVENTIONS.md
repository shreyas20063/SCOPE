# Coding Conventions

**Analysis Date:** 2026-03-27

## Naming Patterns

**Files (Python):**
- Simulators: `snake_case.py` matching the simulation ID (e.g., `backend/simulations/rc_lowpass_filter.py` for ID `rc_lowpass_filter`)
- Core modules: `snake_case.py` (e.g., `backend/core/executor.py`, `backend/core/data_handler.py`)
- Routes: `snake_case.py` (e.g., `backend/routes/hub.py`)

**Files (JavaScript):**
- Components: `PascalCase.jsx` (e.g., `frontend/src/components/RCLowpassViewer.jsx`)
- Hooks: `camelCase.js` prefixed with `use` (e.g., `frontend/src/hooks/useSimulation.js`)
- Services: `camelCase.js` (e.g., `frontend/src/services/api.js`)
- Styles: `PascalCase.css` matching component name (e.g., `frontend/src/styles/RCLowpassViewer.css`)
- Pages: `PascalCase.jsx` (e.g., `frontend/src/pages/SimulationPage.jsx`)

**Python Classes:**
- Simulator classes: `PascalCase` + `Simulator` suffix (e.g., `RCLowpassSimulator`, `NonlinearControlLabSimulator`)
- Exception classes: `PascalCase` (e.g., `ExecutionTimeout`, `ExecutionError`)
- Base class: `BaseSimulator` in `backend/simulations/base_simulator.py`

**Python Functions/Methods:**
- `snake_case` throughout (e.g., `get_or_create_simulator`, `update_parameter`, `get_plots`)
- Private methods: prefix with `_` (e.g., `_compute()`, `_validate_param()`, `_parse_coeffs()`)
- Class constants: `UPPER_SNAKE_CASE` (e.g., `PARAMETER_SCHEMA`, `DEFAULT_PARAMS`, `HUB_SLOTS`)

**JavaScript Functions:**
- `camelCase` for all functions and callbacks (e.g., `handleError`, `validateParam`, `updateParameter`)
- React components: `PascalCase` (e.g., `RCPlot`, `SimulationViewer`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEBOUNCE_WAIT`, `API_TIMEOUT`, `ANIMATION_BASE_INTERVAL`)

**Variables:**
- Python: `snake_case` (e.g., `active_simulators`, `simulation_cache`)
- JavaScript: `camelCase` (e.g., `currentParams`, `isLoading`, `pendingUpdates`)
- React refs: `camelCase` + `Ref` suffix (e.g., `mountedRef`, `animationIntervalRef`, `isFlushingRef`)

**Types/Schemas:**
- Python type hints on all function signatures using `typing` module
- `Dict[str, Any]`, `List[Dict]`, `Optional[...]` patterns throughout
- Pydantic models for API request bodies in `backend/main.py`

## Code Style

**Formatting:**
- No dedicated formatter config detected (no `.prettierrc`, `.eslintrc`, `biome.json`)
- Python: 4-space indentation, ~100 char line width observed
- JavaScript: 2-space indentation, single quotes for imports, template literals for string interpolation

**Linting:**
- No explicit linter configuration detected
- Follow existing patterns: Google-style docstrings in Python, JSDoc in JavaScript

## Import Organization

**Python (follow this order):**
1. Standard library (`import os`, `import time`, `import threading`)
2. Third-party packages (`import numpy as np`, `from fastapi import ...`, `from scipy import ...`)
3. Local/project imports (`from .base_simulator import BaseSimulator`, `from core.executor import ...`)

Example from `backend/main.py`:
```python
import time
import asyncio
import logging
import threading

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import CORS_SETTINGS, API_PREFIX
from core.executor import SimulationExecutor
from core.data_handler import DataHandler
from simulations.catalog import get_all_simulations, get_simulation_by_id
```

**JavaScript (follow this order):**
1. React and React libraries (`import React, { useState, useCallback } from 'react'`)
2. Third-party packages (`import Plot from 'react-plotly.js'`, `import axios from 'axios'`)
3. Local components and hooks (`import PlotDisplay from './PlotDisplay'`, `import useHub from '../hooks/useHub'`)
4. CSS imports (`import '../styles/SimulationViewer.css'`)

**Path Aliases:**
- No path aliases configured in `vite.config.js`
- Use relative paths: `../hooks/useSimulation`, `./PlotDisplay`, `../services/api`

## Error Handling

**Backend API Pattern:**
- All simulator output passes through `DataHandler.serialize_result()` before JSON response
- `SimulationExecutor` wraps all simulator calls with timeout (30s) and returns `{success, data, error, details}` dicts
- `get_or_create_simulator()` in `backend/main.py` catches all exceptions, logs with `exc_info=True`, returns `None` on failure
- FastAPI endpoints raise `HTTPException` for client errors (400, 404, 422)
- Rate limiting returns 429 JSON responses (currently disabled)

**Backend Simulator Pattern:**
- `_validate_param()` in `BaseSimulator` silently clamps out-of-range values (no exceptions)
- `handle_action()` in complex simulators catches ALL exceptions into `self._error` attribute
- Always check error state after calling `handle_action()`

**Frontend API Pattern:**
- `ApiClient` class in `frontend/src/services/api.js` wraps all axios calls in try/catch
- Returns `{success: boolean, data?, error?, details?, status?}` objects -- never throws
- `handleError()` function distinguishes: response errors, network errors, setup errors
- 30s timeout on all API calls, 5s timeout on hub validation calls

**Frontend Component Pattern:**
- `useSimulation` hook manages loading/error/updating states via `useState`
- Refs (`mountedRef`, `isFlushingRef`) prevent state updates on unmounted components
- Debounced parameter updates (150ms) prevent API flooding

## Logging

**Framework:** Python `logging` module

**Patterns:**
- Logger per module: `logger = logging.getLogger(__name__)` in `backend/main.py`
- `logger.info()` for startup/shutdown events
- `logger.error()` with `exc_info=True` for simulator failures
- `logger.warning()` for non-critical issues (cleanup errors)
- `logger.debug()` for periodic maintenance events
- Frontend: `console.log` in development (stripped in production build via terser `drop_console: true`)

## Comments

**When to Comment:**
- Module-level docstrings required on all Python files (triple-quote at top)
- Class-level docstrings explaining purpose and key parameters
- Method-level Google-style docstrings with Args/Returns/Raises sections

**JSDoc:**
- Function-level JSDoc with `@param` and `@returns` tags on hooks and API methods
- Component-level JSDoc describing purpose

**Python Docstring Pattern (Google-style):**
```python
def execute(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Execute a function with timeout protection and error handling.

    Args:
        func: The function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Dict with keys:
            - success: bool
            - data: Any (result if successful)
            - error: str or None
    """
```

**JavaScript JSDoc Pattern:**
```javascript
/**
 * Custom hook for managing simulation state
 * @param {string} simId - Simulation ID
 * @returns {Object} Simulation state and methods
 */
```

## Function Design

**Size:** Simulators can be large (500-2000+ lines) but use private helper methods for computation. Keep public API methods thin: `get_state()`, `update_parameter()`, `get_plots()`.

**Parameters:**
- Python: keyword arguments with type hints and defaults. Use `Optional[Dict[str, Any]] = None` pattern.
- JavaScript: destructured props for components, named parameters for utility functions.

**Return Values:**
- Backend always returns dicts with `success`, `data`, `error` keys from endpoints
- Simulators return `{parameters, plots, metadata}` dicts from `get_state()`
- Plots are always lists of `{id, title, data, layout}` Plotly dicts

## Module Design

**Exports (Python):**
- `backend/simulations/__init__.py` maintains `SIMULATOR_REGISTRY` dict and `__all__` list
- Every simulator class must be imported, registered, and added to `__all__`
- Utility functions: `get_simulator_class()`, `is_simulator_available()`, `register_simulator()`

**Exports (JavaScript):**
- Named exports for hooks: `export function useSimulation(simId) { ... }`
- Default exports for components: `export default RCLowpassViewer`
- Class export for API: `export default new ApiClient()` (singleton instance)

**Barrel Files:**
- `backend/simulations/__init__.py` is the only barrel file; it centralizes all simulator imports

## CSS Conventions

**Variables Required:**
- All colors, spacing, shadows, radii, and transitions MUST use CSS variables from `frontend/src/styles/App.css` `:root`
- Never hardcode colors -- use `var(--primary-color)`, `var(--text-secondary)`, etc.
- Never hardcode border-radius -- use `var(--radius-sm)` through `var(--radius-xl)`
- Never hardcode transitions -- use `var(--transition-fast)`, `var(--transition-normal)`, `var(--transition-slow)`

**Theme Support:**
- Dark mode is default; light mode overrides in `[data-theme="light"]` blocks
- Theme detection: `document.documentElement.getAttribute('data-theme') || 'dark'`
- Components needing theme reactivity use MutationObserver on `data-theme` attribute

**Component CSS:**
- Each custom viewer has its own CSS file in `frontend/src/styles/`
- File name matches component: `RCLowpassViewer.jsx` -> `RCLowpassViewer.css` (or imported as `./RCLowpassViewer.css`)
- No CSS modules -- plain CSS with class-based selectors
- BEM-like naming not enforced; classes are descriptive (e.g., `.simulation-viewer`, `.control-panel`, `.plot-container`)

**Responsive Breakpoints:**
- Mobile: 768px
- Tablet: 1024px
- Use `@media (max-width: 768px)` for mobile-specific layouts

## Plotly Plot Conventions

**Color Palette for Traces:**
- Blue `#3b82f6` -- input signal, primary trace
- Red `#ef4444` -- output signal, secondary trace
- Green `#10b981` -- reference lines, cutoff markers
- Teal `#14b8a6` -- accent traces

**Layout Pattern (follow exactly):**
```javascript
{
  paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
  plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
  font: { family: 'Inter, sans-serif', size: 12 },
  xaxis: { gridcolor: 'rgba(148,163,184,0.1)', zerolinecolor: 'rgba(148,163,184,0.3)' },
  margin: { t: 45, r: 25, b: 55, l: 60 },
  datarevision: `${id}-${title}-${Date.now()}`,  // forces re-render
  uirevision: id,                                 // preserves zoom/pan
}
```

## Simulator Implementation Pattern

**Every simulator must:**
1. Extend `BaseSimulator` from `backend/simulations/base_simulator.py`
2. Define `PARAMETER_SCHEMA` dict (control types: slider, select, checkbox, button, expression)
3. Define `DEFAULT_PARAMS` dict
4. Implement `initialize(params)`, `update_parameter(name, value)`, `get_plots()`, `get_state()`
5. Use `_validate_param()` inherited from base class for parameter clamping
6. Include `simulation_type` key in `get_state()` metadata for custom viewer matching
7. Use NumPy vectorized operations -- no Python for-loops on arrays

**NumPy Compatibility:**
- `np.trapz` is deprecated in NumPy 2.0+. Use: `_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz`

**Hub Integration (optional):**
- Define `HUB_SLOTS: List[str]` (e.g., `['control']`, `['signal']`)
- Define `HUB_DOMAIN: str` (`"ct"` or `"dt"`)
- Define `HUB_DIMENSIONS: Dict` (`{"n": None, "m": 1, "p": 1}` for SISO)
- Override `to_hub_data()` and `from_hub_data()` if non-standard parameter names

## React Component Pattern

**Functional components only** -- no class components.

**Hook usage:**
- `useState` for local state
- `useCallback` for memoized callbacks (especially parameter update handlers)
- `useMemo` for expensive computations (plot layout objects)
- `useRef` for mutable values that don't trigger re-renders (animation timers, lock flags)
- `useEffect` for side effects (API calls, subscriptions, cleanup)

**Lazy Loading:**
- Heavy components (Three.js viewers, complex Plotly viewers) use `React.lazy(() => import('./Component'))`
- Wrapped in `<Suspense fallback={<div>Loading...</div>}>` in `SimulationViewer.jsx`
- Three.js excluded from Vite `optimizeDeps` for on-demand loading

**Viewer Chain Pattern:**
- `SimulationViewer.jsx` (~2242 lines) dispatches to custom viewers based on `metadata?.simulation_type`
- Custom viewers receive `{metadata, plots, ...}` props
- If no custom viewer matches, falls back to generic `PlotDisplay.jsx`

---

*Convention analysis: 2026-03-27*
