/**
 * ControlPanel Component
 *
 * Renders dynamic controls based on parameter definitions from backend.
 * Supports: sliders, number inputs, selects, checkboxes, buttons, and expressions.
 *
 * Enhanced for convolution simulator with:
 * - Expression input for custom signals
 * - Visibility logic for conditional controls
 * - Step navigation buttons
 * - Demo preset selector with descriptions
 */

import { useCallback, useMemo, useRef, useState, useEffect } from 'react';
import '../styles/ControlPanel.css';

/**
 * Display transform functions for non-linear slider mappings
 * These convert raw slider values to human-readable display values
 */
const displayTransforms = {
  // Q factor logarithmic mapping: slider 0-100 maps to Q 0.1-10
  // Q = 10^((slider/50) - 1)
  // slider=0 → Q=0.1, slider=50 → Q=1.0, slider=100 → Q=10.0
  q_log: (sliderValue) => {
    const Q = Math.pow(10, (sliderValue / 50.0) - 1.0);
    return Q;
  },
};

// Horizontal travel (px) after which a touch on a slider counts as a drag
const TOUCH_SLOP_PX = 6;

/**
 * Slider Control - Simple controlled slider with local state
 */
function SliderControl({ param, value, onChange, disabled }) {
  const [localValue, setLocalValue] = useState(value ?? param.default ?? param.min);
  const [dragEndCount, setDragEndCount] = useState(0);
  const isDragging = useRef(false);
  const activePointerId = useRef(null);
  // Touch that has not yet shown it is a slider gesture: { x, y, held }
  const pendingTouch = useRef(null);
  const removeWindowListeners = useRef(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  // Sync with external value when not dragging, and once more when a drag ends
  // so a value changed elsewhere mid-drag (preset, reset, backend) shows up.
  useEffect(() => {
    if (!isDragging.current) {
      setLocalValue(value ?? param.default ?? param.min);
    }
  }, [value, param.default, param.min, dragEndCount]);

  const commitPendingTouch = useCallback(() => {
    const touch = pendingTouch.current;
    pendingTouch.current = null;
    if (touch && touch.held !== undefined) {
      onChangeRef.current(param.name, touch.held);
    }
  }, [param.name]);

  // End a drag however the pointer is released: pointerup/cancel on the input,
  // lost pointer capture, or a release outside the input (window listener).
  const endDrag = useCallback((e) => {
    if (e && activePointerId.current !== null && e.pointerId !== undefined &&
        e.pointerId !== activePointerId.current) {
      return;
    }
    if (removeWindowListeners.current) {
      removeWindowListeners.current();
      removeWindowListeners.current = null;
    }
    // A touch released with pointerup was a tap or a horizontal drag: apply it.
    // A pointercancel means the browser took the touch over to scroll the page,
    // so the held value is dropped and the re-sync puts the thumb back.
    if (e && e.type === 'pointerup') commitPendingTouch();
    pendingTouch.current = null;
    activePointerId.current = null;
    if (!isDragging.current) return;
    isDragging.current = false;
    setDragEndCount((n) => n + 1);
  }, [commitPendingTouch]);

  useEffect(() => () => removeWindowListeners.current?.(), []);

  const handleInput = (e) => {
    const newValue = parseFloat(e.target.value);
    setLocalValue(newValue);
    // Chrome jumps the thumb to the finger on touchstart, before it knows
    // whether the gesture is a vertical page scroll (touch-action: pan-y).
    // Hold the update until the touch proves to be a slider gesture.
    if (pendingTouch.current) {
      pendingTouch.current.held = newValue;
      return;
    }
    onChange(param.name, newValue);
  };

  const handlePointerDown = (e) => {
    isDragging.current = true;
    activePointerId.current = e.pointerId;
    pendingTouch.current = e.pointerType === 'touch'
      ? { x: e.clientX, y: e.clientY, held: undefined }
      : null;
    if (!removeWindowListeners.current) {
      window.addEventListener('pointerup', endDrag);
      window.addEventListener('pointercancel', endDrag);
      removeWindowListeners.current = () => {
        window.removeEventListener('pointerup', endDrag);
        window.removeEventListener('pointercancel', endDrag);
      };
    }
  };

  const handlePointerMove = (e) => {
    const touch = pendingTouch.current;
    if (!touch || e.pointerId !== activePointerId.current) return;
    const dx = Math.abs(e.clientX - touch.x);
    const dy = Math.abs(e.clientY - touch.y);
    if (dx > TOUCH_SLOP_PX && dx >= dy) commitPendingTouch();
  };

  const percentage = useMemo(() => {
    const range = param.max - param.min;
    return ((localValue - param.min) / range) * 100;
  }, [localValue, param.min, param.max]);

  // Apply display transform if specified (e.g., for non-linear Q slider)
  const displayValue = useMemo(() => {
    if (param.display_transform && displayTransforms[param.display_transform]) {
      return displayTransforms[param.display_transform](localValue);
    }
    return localValue;
  }, [localValue, param.display_transform]);

  const sliderTitle = `${param.label || param.name}: ${param.min} – ${param.max}${param.unit ? ` ${param.unit}` : ''}`;

  return (
    <div className="control-group" title={sliderTitle}>
      <div className="control-header">
        <label htmlFor={param.name} className="control-label">
          {param.label || param.name}
        </label>
        <span className="control-value">
          {typeof displayValue === 'number' ? displayValue.toFixed(2) : displayValue}
          {param.unit && <span className="control-unit"> {param.unit}</span>}
        </span>
      </div>
      <div className="slider-container" style={{ '--slider-percentage': `${percentage}%` }}>
        <input
          type="range"
          id={param.name}
          name={param.name}
          min={param.min}
          max={param.max}
          step={param.step || 1}
          value={localValue}
          onInput={handleInput}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
          onLostPointerCapture={endDrag}
          disabled={disabled}
          className="slider-input"
        />
        <div className="slider-range">
          <span>{param.display_transform && displayTransforms[param.display_transform]
            ? displayTransforms[param.display_transform](param.min).toFixed(1)
            : param.min}</span>
          <span>{param.display_transform && displayTransforms[param.display_transform]
            ? displayTransforms[param.display_transform](param.max).toFixed(1)
            : param.max}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Number Input Control
 */
function NumberControl({ param, value, onChange, disabled }) {
  const handleChange = (e) => {
    const newValue = parseFloat(e.target.value);
    if (!isNaN(newValue)) {
      onChange(param.name, newValue);
    }
  };

  return (
    <div className="control-group">
      <label htmlFor={param.name} className="control-label">
        {param.label || param.name}
        {param.unit && <span className="control-unit"> ({param.unit})</span>}
      </label>
      <div className="number-input-container">
        <input
          type="number"
          id={param.name}
          name={param.name}
          min={param.min}
          max={param.max}
          step={param.step || 1}
          value={value ?? param.default ?? 0}
          onChange={handleChange}
          disabled={disabled}
          className="number-input"
        />
      </div>
    </div>
  );
}

/**
 * Select Control with optional description display
 */
function SelectControl({ param, value, onChange, disabled, metadata }) {
  const handleChange = (e) => {
    onChange(param.name, e.target.value);
  };

  // For demo_preset, get dynamic options from metadata
  const options = useMemo(() => {
    // Check if this is demo_preset and we have metadata with presets
    if (param.name === 'demo_preset' && metadata?.demo_presets?.presets) {
      return metadata.demo_presets.presets.map(p => ({
        value: p.value,
        label: p.label,
        description: p.description
      }));
    }

    return (param.options || []).map(opt => {
      if (typeof opt === 'object') {
        return { value: opt.value, label: opt.label || opt.value, description: opt.description };
      }
      return { value: opt, label: opt };
    });
  }, [param.options, param.name, metadata]);

  // Get current selection description
  const currentDescription = useMemo(() => {
    const current = options.find(o => o.value === value);
    return current?.description;
  }, [options, value]);

  return (
    <div className="control-group">
      <label htmlFor={param.name} className="control-label">
        {param.label || param.name}
      </label>
      <select
        id={param.name}
        name={param.name}
        value={value ?? param.default ?? ''}
        onChange={handleChange}
        disabled={disabled}
        className="select-input"
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {currentDescription && (
        <div className="control-description">{currentDescription}</div>
      )}
    </div>
  );
}

/**
 * Checkbox Control
 */
function CheckboxControl({ param, value, onChange, disabled }) {
  const handleChange = (e) => {
    onChange(param.name, e.target.checked);
  };

  return (
    <div className="control-group control-checkbox">
      <label className="checkbox-label">
        <input
          type="checkbox"
          id={param.name}
          name={param.name}
          checked={value ?? param.default ?? false}
          onChange={handleChange}
          disabled={disabled}
          className="checkbox-input"
        />
        <span className="checkbox-custom"></span>
        <span className="checkbox-text">{param.label || param.name}</span>
      </label>
    </div>
  );
}

/**
 * Expression Input Control for custom signal expressions
 */
function ExpressionControl({ param, value, onChange, disabled, mode }) {
  const [localValue, setLocalValue] = useState(value ?? param.default ?? '');
  const [error, setError] = useState(null);
  const debounceRef = useRef(null);

  // Sync with external value
  useEffect(() => {
    setLocalValue(value ?? param.default ?? '');
  }, [value, param.default]);

  // Client-side validation
  const validateExpression = (expr) => {
    if (!expr || !expr.trim()) return 'Expression required';

    // Security checks
    const dangerous = ['import', 'exec', 'eval', '__', 'open', 'os.', 'sys.'];
    for (const pattern of dangerous) {
      if (expr.toLowerCase().includes(pattern)) {
        return `Unsafe pattern: ${pattern}`;
      }
    }

    // Balance checks
    if ((expr.match(/\(/g) || []).length !== (expr.match(/\)/g) || []).length) {
      return 'Unbalanced parentheses';
    }
    if ((expr.match(/\[/g) || []).length !== (expr.match(/\]/g) || []).length) {
      return 'Unbalanced brackets';
    }

    return null;
  };

  const handleChange = (e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);

    // Validate locally
    const validationError = validateExpression(newValue);
    setError(validationError);

    // Debounce the API call
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (!validationError) {
        onChange(param.name, newValue);
      }
    }, 500);
  };

  const handleBlur = () => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const validationError = validateExpression(localValue);
    if (!validationError) {
      onChange(param.name, localValue);
    }
  };

  // Get hints based on mode
  const hints = useMemo(() => {
    if (mode === 'discrete') {
      return 'Format: [1, 2, 1] or 0.5**n * u(n)';
    }
    return 'Functions: u(t), rect(t), tri(t), exp(t), sin(t)';
  }, [mode]);

  return (
    <div className={`control-group ${error ? 'has-error' : ''}`}>
      <label htmlFor={param.name} className="control-label">
        {param.label || param.name}
      </label>
      <input
        type="text"
        id={param.name}
        name={param.name}
        value={localValue}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder={param.placeholder || 'Enter expression...'}
        disabled={disabled}
        className="expression-input"
        spellCheck={false}
        autoComplete="off"
      />
      {error && <div className="expression-error">{error}</div>}
      <div className="expression-hints">{hints}</div>
    </div>
  );
}

/**
 * Button Control with special handling for play_pause and step buttons
 */
function ButtonControl({ param, onClick, onStepForward, onStepBackward, disabled, isRunning, actionPending }) {
  const buttonName = param.name;

  // Special handling for play/pause button
  if (buttonName === 'play_pause') {
    return (
      <div className="control-group playback-button">
        <button
          type="button"
          onClick={() => onClick(buttonName)}
          disabled={disabled}
          className={`control-button ${isRunning ? 'control-button-pause' : 'control-button-play'}`}
        >
          {isRunning ? '⏸ Pause' : '▶ Play'}
        </button>
      </div>
    );
  }

  // Step backward button
  if (buttonName === 'step_backward') {
    return (
      <div className="control-group step-button-group">
        <button
          type="button"
          onClick={onStepBackward}
          disabled={disabled}
          className="control-button step-button step-backward"
          title="Step backward (Left Arrow)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
          Step
        </button>
      </div>
    );
  }

  // Step forward button
  if (buttonName === 'step_forward') {
    return (
      <div className="control-group step-button-group">
        <button
          type="button"
          onClick={onStepForward}
          disabled={disabled}
          className="control-button step-button step-forward"
          title="Step forward (Right Arrow)"
        >
          Step
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>
      </div>
    );
  }

  // Generic action button. While an action is in flight it is locked with
  // aria-disabled (clicks are ignored by ControlPanel) rather than `disabled`,
  // so keyboard focus stays on it.
  return (
    <div className="control-group">
      <button
        type="button"
        onClick={() => onClick(buttonName)}
        disabled={disabled}
        aria-disabled={actionPending || undefined}
        className="control-button"
      >
        {param.label || param.name}
      </button>
    </div>
  );
}

/**
 * Check if a control should be visible based on visibility conditions
 */
function shouldShowControl(param, currentValues) {
  // If explicitly hidden, never show
  if (param.hidden) return false;

  // If no visibility condition, always show
  if (!param.visible_when) return true;

  // Check all conditions (supports array values for OR matching)
  return Object.entries(param.visible_when).every(([key, expectedValue]) => {
    if (Array.isArray(expectedValue)) {
      return expectedValue.includes(currentValues[key]);
    }
    return currentValues[key] === expectedValue;
  });
}

/**
 * Control renderer - selects appropriate control type
 */
function Control({ param, value, onChange, onButtonClick, onStepForward, onStepBackward, disabled, isRunning, actionPending, mode, metadata }) {
  switch (param.type) {
    case 'slider':
      return (
        <SliderControl
          param={param}
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case 'number_input':
    case 'number':
      return (
        <NumberControl
          param={param}
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case 'select':
      return (
        <SelectControl
          param={param}
          value={value}
          onChange={onChange}
          disabled={disabled}
          metadata={metadata}
        />
      );

    case 'checkbox':
      return (
        <CheckboxControl
          param={param}
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
      );

    case 'expression':
      return (
        <ExpressionControl
          param={param}
          value={value}
          onChange={onChange}
          disabled={disabled}
          mode={mode}
        />
      );

    case 'button':
      return (
        <ButtonControl
          param={param}
          onClick={onButtonClick}
          onStepForward={onStepForward}
          onStepBackward={onStepBackward}
          disabled={disabled}
          isRunning={isRunning}
          actionPending={actionPending}
        />
      );

    default:
      // Default to number input for unknown types
      return (
        <NumberControl
          param={param}
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
      );
  }
}

/**
 * Main ControlPanel component
 */
function ControlPanel({
  parameters = [],
  currentValues = {},
  onParamChange,
  onReset,
  onButtonClick,
  onStepForward,
  onStepBackward,
  isLoading = false,
  isUpdating = false,
  isRunning = false,
  metadata = null,
}) {
  // Get current mode for expression hints
  const mode = currentValues.mode || 'continuous';

  // Group parameters by their group property, filtering by visibility
  const groupedParams = useMemo(() => {
    const groups = {};
    parameters.forEach(param => {
      // Check visibility
      if (!shouldShowControl(param, currentValues)) {
        return; // Skip hidden controls
      }

      const group = param.group || 'Parameters';
      if (!groups[group]) {
        groups[group] = [];
      }
      groups[group].push(param);
    });
    return groups;
  }, [parameters, currentValues]);

  const handleChange = useCallback((paramName, value) => {
    if (onParamChange) {
      onParamChange(paramName, value);
    }
  }, [onParamChange]);

  const handleReset = useCallback(() => {
    if (onReset) {
      onReset();
    }
  }, [onReset]);

  // Action buttons (every button except play/pause and the step buttons,
  // which have their own guards) start backend work that can take tens of
  // seconds, e.g. compute_roa. The backend runs it on its event loop, so a
  // duplicate click would block every request for another full compute.
  // Lock action buttons until the running one finishes; the ref makes the
  // guard synchronous, the state drives aria-disabled.
  const actionInFlightRef = useRef(false);
  const [actionInFlight, setActionInFlight] = useState(false);

  const handleButtonClick = useCallback(async (buttonName) => {
    const handler = onButtonClick || handleChange;
    if (buttonName === 'play_pause') {
      handler(buttonName);
      return;
    }
    if (actionInFlightRef.current) return;
    actionInFlightRef.current = true;
    setActionInFlight(true);
    try {
      await handler(buttonName);
    } finally {
      actionInFlightRef.current = false;
      setActionInFlight(false);
    }
  }, [onButtonClick, handleChange]);

  if (!parameters || parameters.length === 0) {
    return (
      <div className="control-panel">
        <div className="control-panel-empty">
          <p>No parameters available for this simulation.</p>
        </div>
      </div>
    );
  }

  // Only block input during the initial load. Background updates must not
  // disable controls: a disabled input aborts an in-progress drag (pointer
  // capture is dropped) and throws keyboard focus to <body>. useSimulation
  // already serializes parameter updates and queues edits made while one is
  // in flight; action buttons are locked separately (handleButtonClick).
  const disabled = isLoading;

  return (
    <div
      className={`control-panel ${disabled ? 'control-panel-disabled' : ''}`}
      aria-busy={isLoading || isUpdating}
    >
      <div className="control-panel-header">
        <h3>Parameters</h3>
        {isUpdating && (
          <span className="updating-indicator">
            <span className="updating-dot"></span>
            Updating...
          </span>
        )}
      </div>

      <div className="control-panel-content">
        {Object.entries(groupedParams).map(([groupName, groupParams]) => (
          <div key={groupName} className={`control-group-section ${groupName === 'Playback' ? 'playback-section' : ''}`}>
            <h4 className="control-group-title">{groupName}</h4>
            <div className={groupName === 'Playback' ? 'playback-controls-row' : ''}>
              {groupParams.map(param => (
                <Control
                  key={param.name}
                  param={param}
                  value={currentValues[param.name]}
                  onChange={handleChange}
                  onButtonClick={handleButtonClick}
                  onStepForward={onStepForward}
                  onStepBackward={onStepBackward}
                  disabled={disabled}
                  isRunning={isRunning}
                  actionPending={actionInFlight}
                  mode={mode}
                  metadata={metadata}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Error display */}
      {metadata?.error && (
        <div className="control-panel-error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          {metadata.error}
        </div>
      )}

      <div className="control-panel-footer">
        <button
          type="button"
          onClick={handleReset}
          disabled={disabled}
          className="btn btn-reset"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          Reset to Defaults
        </button>
      </div>
    </div>
  );
}

export default ControlPanel;
