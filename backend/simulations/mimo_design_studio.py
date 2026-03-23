"""MIMO Design Studio Simulator — Analysis Mode

Interactive state-space analysis for MIMO systems. Provides presets for
real-world multi-input multi-output plants (aircraft lateral, coupled spring-mass,
DC motor + flexible load), matrix parsing, eigenvalue analysis, controllability/
observability assessment, and step/impulse response grid plots.

Controller design modes (pole placement, LQR, LQG) are placeholders in this
module and will be implemented in Task 3.

Reference: Ogata Ch.12 (MIMO), Friedland Ch.3-4 (state-space),
Etkin & Reid (aircraft lateral dynamics).
"""

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import signal

from core.mimo_utils import (
    controllability_matrix,
    observability_matrix,
    mimo_step_response,
    mimo_impulse_response,
    validate_dimensions,
)
from .base_simulator import BaseSimulator


class MIMODesignStudioSimulator(BaseSimulator):
    """MIMO state-space analysis and controller design studio.

    Supports analysis mode (eigenvalues, controllability, observability,
    step/impulse response grids) with three physical presets and custom
    matrix entry.
    """

    # ------------------------------------------------------------------ #
    #  Presets                                                            #
    # ------------------------------------------------------------------ #

    _PRESETS: Dict[str, Dict[str, Any]] = {
        "aircraft_lateral": {
            "name": "Aircraft Lateral Dynamics",
            "A": [
                [-0.322, 0.064, 0.0364, -0.9917],
                [0.0, -0.465, 0.0121, 0.0],
                [-0.0150, -0.624, -0.275, 0.0],
                [0.0, 0.018, 0.318, 0.0],
            ],
            "B": [
                [0.0, 0.0064],
                [-0.161, 0.0028],
                [0.0, -0.264],
                [0.0, 0.0],
            ],
            "C": [
                [1, 0, 0, 0],
                [0, 0, 0, 1],
            ],
            "D": [
                [0, 0],
                [0, 0],
            ],
            "state_names": ["\u03b2", "p", "r", "\u03c6"],
            "input_names": ["\u03b4a", "\u03b4r"],
            "output_names": ["\u03b2", "\u03c6"],
        },
        "coupled_spring_mass": {
            "name": "Coupled Mass-Spring-Damper",
            "A": [
                [0, 1, 0, 0],
                [-2.5, -0.3, 0.5, 0],
                [0, 0, 0, 1],
                [0.5, 0, -1.5, -0.3],
            ],
            "B": [
                [0, 0],
                [1, 0],
                [0, 0],
                [0, 1],
            ],
            "C": [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
            ],
            "D": [
                [0, 0],
                [0, 0],
            ],
            "state_names": ["x\u2081", "v\u2081", "x\u2082", "v\u2082"],
            "input_names": ["F\u2081", "F\u2082"],
            "output_names": ["x\u2081", "x\u2082"],
        },
        "dc_motor_flex": {
            "name": "DC Motor + Flexible Load",
            "A": [
                [0, 1, 0, 0],
                [-100, -11, 100, 0],
                [0, 0, 0, 1],
                [20, 0, -20, -2],
            ],
            "B": [
                [0],
                [10],
                [0],
                [0],
            ],
            "C": [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
            ],
            "D": [
                [0],
                [0],
            ],
            "state_names": ["\u03b8m", "\u03c9m", "\u03b8L", "\u03c9L"],
            "input_names": ["V"],
            "output_names": ["\u03b8m", "\u03b8L"],
        },
    }

    # ------------------------------------------------------------------ #
    #  Parameter schema & defaults                                       #
    # ------------------------------------------------------------------ #

    # Default matrix strings for aircraft lateral preset
    _DEFAULT_A = "-0.322, 0.064, 0.0364, -0.9917; 0, -0.465, 0.0121, 0; -0.015, -0.624, -0.275, 0; 0, 0.018, 0.318, 0"
    _DEFAULT_B = "0, 0.0064; -0.161, 0.0028; 0, -0.264; 0, 0"
    _DEFAULT_C = "1, 0, 0, 0; 0, 0, 0, 1"
    _DEFAULT_D = "0, 0; 0, 0"

    PARAMETER_SCHEMA: Dict[str, Dict] = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "aircraft_lateral", "label": "Aircraft Lateral Dynamics"},
                {"value": "coupled_spring_mass", "label": "Coupled Mass-Spring-Damper"},
                {"value": "dc_motor_flex", "label": "DC Motor + Flexible Load"},
                {"value": "custom", "label": "Custom Matrices"},
            ],
            "default": "aircraft_lateral",
        },
        "matrix_a": {"type": "expression", "default": _DEFAULT_A},
        "matrix_b": {"type": "expression", "default": _DEFAULT_B},
        "matrix_c": {"type": "expression", "default": _DEFAULT_C},
        "matrix_d": {"type": "expression", "default": _DEFAULT_D},
        "design_mode": {
            "type": "select",
            "options": [
                {"value": "analysis", "label": "Analysis"},
                {"value": "pole_placement", "label": "Pole Placement"},
                {"value": "lqr", "label": "LQR Optimal"},
                {"value": "lqg", "label": "LQG (LQR + Kalman)"},
            ],
            "default": "analysis",
        },
        "desired_poles": {
            "type": "expression",
            "default": "-1, -2, -3+1j, -3-1j",
        },
        "q_diag": {
            "type": "expression",
            "default": "1, 1, 1, 1",
        },
        "r_diag": {
            "type": "expression",
            "default": "1, 1",
        },
        "qw_diag": {
            "type": "expression",
            "default": "0.1, 0.1, 0.1, 0.1",
        },
        "rv_diag": {
            "type": "expression",
            "default": "1, 1",
        },
        "time_span": {
            "type": "slider",
            "min": 1,
            "max": 50,
            "step": 1,
            "default": 10,
        },
        "step_input_channel": {
            "type": "slider",
            "min": 0,
            "max": 7,
            "step": 1,
            "default": 0,
        },
        "compute_controller": {
            "type": "button",
            "default": False,
        },
    }

    DEFAULT_PARAMS: Dict[str, Any] = {
        "preset": "aircraft_lateral",
        "matrix_a": _DEFAULT_A,
        "matrix_b": _DEFAULT_B,
        "matrix_c": _DEFAULT_C,
        "matrix_d": _DEFAULT_D,
        "design_mode": "analysis",
        "desired_poles": "-1, -2, -3+1j, -3-1j",
        "q_diag": "1, 1, 1, 1",
        "r_diag": "1, 1",
        "qw_diag": "0.1, 0.1, 0.1, 0.1",
        "rv_diag": "1, 1",
        "time_span": 10,
        "step_input_channel": 0,
        "compute_controller": False,
    }

    _MAX_EXPR_LEN = 512
    _MAX_N = 8  # max state dimension
    _MAX_M = 4  # max input dimension
    _MAX_P = 4  # max output dimension
    _N_TIME_POINTS = 500

    # ------------------------------------------------------------------ #
    #  Initialization & parameter handling                               #
    # ------------------------------------------------------------------ #

    def _validate_expression(self, name: str, value: str) -> str:
        """Clamp expression strings to _MAX_EXPR_LEN and strip whitespace."""
        value = str(value).strip()
        if len(value) > self._MAX_EXPR_LEN:
            raise ValueError(
                f"Expression '{name}' is too long "
                f"(max {self._MAX_EXPR_LEN} characters)."
            )
        return value

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with merged parameters; apply preset if not custom.

        Args:
            params: Optional parameter overrides.
        """
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in list(self.parameters.items()):
            schema = self.PARAMETER_SCHEMA.get(name, {})
            if schema.get("type") == "expression":
                self.parameters[name] = self._validate_expression(name, value)
            else:
                self.parameters[name] = self._validate_param(name, value)

        preset = self.parameters.get("preset", "aircraft_lateral")
        if preset != "custom":
            self._apply_preset(preset)
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and return updated state.

        Args:
            name: Parameter name.
            value: New parameter value.

        Returns:
            Full simulation state dict.
        """
        if name not in self.parameters:
            return self.get_state()

        schema = self.PARAMETER_SCHEMA.get(name, {})
        if schema.get("type") == "expression":
            self.parameters[name] = self._validate_expression(name, value)
        else:
            self.parameters[name] = self._validate_param(name, value)

        # Preset change: auto-fill matrix expression fields
        if name == "preset" and str(value) != "custom":
            self._apply_preset(str(value))

        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle button actions (compute_controller).

        Args:
            action: Action name.
            params: Current parameter values from frontend.

        Returns:
            Full simulation state dict.
        """
        if params:
            for pname, pval in params.items():
                if pname in self.parameters:
                    schema = self.PARAMETER_SCHEMA.get(pname, {})
                    if schema.get("type") == "expression":
                        self.parameters[pname] = self._validate_expression(
                            pname, pval
                        )
                    else:
                        self.parameters[pname] = self._validate_param(pname, pval)
        return self.get_state()

    def _apply_preset(self, preset_id: str) -> None:
        """Fill matrix expression fields from a preset definition.

        Args:
            preset_id: Key in _PRESETS dict.
        """
        if preset_id not in self._PRESETS:
            return
        preset = self._PRESETS[preset_id]
        self.parameters["matrix_a"] = self._matrix_to_expr(preset["A"])
        self.parameters["matrix_b"] = self._matrix_to_expr(preset["B"])
        self.parameters["matrix_c"] = self._matrix_to_expr(preset["C"])
        self.parameters["matrix_d"] = self._matrix_to_expr(preset["D"])

    @staticmethod
    def _matrix_to_expr(mat: List[List[float]]) -> str:
        """Convert a nested list matrix to semicolon-delimited string.

        Args:
            mat: 2-D list of floats.

        Returns:
            String like '1, 2; 3, 4'.
        """
        rows = []
        for row in mat:
            rows.append(", ".join(str(v) for v in row))
        return "; ".join(rows)

    # ------------------------------------------------------------------ #
    #  Matrix parsing                                                    #
    # ------------------------------------------------------------------ #

    def _parse_matrix(self, expr_str: str, name: str) -> List[List[float]]:
        """Parse a semicolon-delimited matrix expression string.

        Rows split by ';', values by ','.
        Validates: non-empty, float-parseable, uniform column count.

        Args:
            expr_str: Matrix string, e.g. '1, 2; 3, 4'.
            name: Matrix name (for error messages).

        Returns:
            2-D list of floats.

        Raises:
            ValueError: If parsing fails or dimensions are inconsistent.
        """
        expr_str = expr_str.strip()
        if not expr_str:
            raise ValueError(f"Matrix {name} is empty.")

        rows_str = expr_str.split(";")
        matrix: List[List[float]] = []
        ncols: Optional[int] = None

        for i, row_str in enumerate(rows_str):
            row_str = row_str.strip()
            if not row_str:
                continue
            vals_str = row_str.split(",")
            row: List[float] = []
            for v in vals_str:
                v = v.strip()
                if not v:
                    continue
                try:
                    row.append(float(v))
                except ValueError:
                    raise ValueError(
                        f"Matrix {name}: cannot parse '{v}' as float "
                        f"(row {i + 1})."
                    )
            if not row:
                continue
            if ncols is None:
                ncols = len(row)
            elif len(row) != ncols:
                raise ValueError(
                    f"Matrix {name}: row {i + 1} has {len(row)} columns, "
                    f"expected {ncols}."
                )
            matrix.append(row)

        if not matrix:
            raise ValueError(f"Matrix {name} has no valid rows.")
        return matrix

    # ------------------------------------------------------------------ #
    #  Core computation                                                  #
    # ------------------------------------------------------------------ #

    def _compute(self) -> Dict[str, Any]:
        """Main computation dispatcher for analysis mode.

        Parses matrices, validates dimensions, computes eigenvalues,
        controllability, observability, step and impulse responses.

        Returns:
            Dict with all computed data, or dict with 'error' key on failure.
        """
        try:
            # 1. Parse matrices from expression strings
            A_list = self._parse_matrix(self.parameters["matrix_a"], "A")
            B_list = self._parse_matrix(self.parameters["matrix_b"], "B")
            C_list = self._parse_matrix(self.parameters["matrix_c"], "C")
            D_list = self._parse_matrix(self.parameters["matrix_d"], "D")

            A = np.array(A_list, dtype=float)
            B = np.array(B_list, dtype=float)
            C = np.array(C_list, dtype=float)
            D = np.array(D_list, dtype=float)

            # Ensure 2-D
            A = np.atleast_2d(A)
            B = np.atleast_2d(B)
            C = np.atleast_2d(C)
            D = np.atleast_2d(D)

            # 2. Validate dimensions
            dim_err = validate_dimensions(A, B, C, D)
            if dim_err:
                return {"error": dim_err}

            n = A.shape[0]
            m = B.shape[1]
            p = C.shape[0]

            # 3. Check dimension caps
            if n > self._MAX_N:
                return {"error": f"State dimension {n} exceeds max {self._MAX_N}."}
            if m > self._MAX_M:
                return {"error": f"Input dimension {m} exceeds max {self._MAX_M}."}
            if p > self._MAX_P:
                return {"error": f"Output dimension {p} exceeds max {self._MAX_P}."}

            # 4. Eigenvalues
            eigs = np.linalg.eigvals(A)

            # 5. Controllability & observability
            Co = controllability_matrix(A, B)
            Ob = observability_matrix(A, C)
            ctrl_rank = int(np.linalg.matrix_rank(Co))
            obs_rank = int(np.linalg.matrix_rank(Ob))

            # 6. Time vector
            time_span = float(self.parameters.get("time_span", 10))
            t_eval = np.linspace(0, time_span, self._N_TIME_POINTS)

            # 7. Clamp step_input_channel to valid range
            step_ch = int(self.parameters.get("step_input_channel", 0))
            step_ch = max(0, min(step_ch, m - 1))

            # 8. Step and impulse responses (all channels for grid plots)
            step_data = mimo_step_response(A, B, C, D, t_eval)
            impulse_data = mimo_impulse_response(A, B, C, D, t_eval)

            # 9. Preset info
            preset_id = self.parameters.get("preset", "aircraft_lateral")
            preset_info = self._PRESETS.get(preset_id, {})
            preset_name = preset_info.get("name", "Custom")
            state_names = preset_info.get(
                "state_names", [f"x{i+1}" for i in range(n)]
            )
            input_names = preset_info.get(
                "input_names", [f"u{i+1}" for i in range(m)]
            )
            output_names = preset_info.get(
                "output_names", [f"y{i+1}" for i in range(p)]
            )

            # 10. Stability classification
            real_parts = eigs.real
            is_stable = bool(np.all(real_parts < -1e-10))
            is_marginal = bool(
                np.all(real_parts <= 1e-10) and not is_stable
            )

            return {
                "A": A,
                "B": B,
                "C": C,
                "D": D,
                "n": n,
                "m": m,
                "p": p,
                "eigenvalues": eigs,
                "is_stable": is_stable,
                "is_marginal": is_marginal,
                "ctrl_rank": ctrl_rank,
                "obs_rank": obs_rank,
                "step_data": step_data,
                "impulse_data": impulse_data,
                "t_eval": t_eval,
                "preset_id": preset_id,
                "preset_name": preset_name,
                "state_names": state_names,
                "input_names": input_names,
                "output_names": output_names,
                "error": None,
            }

        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------ #
    #  Plot builders                                                     #
    # ------------------------------------------------------------------ #

    def _step_response_grid_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Plotly subplot grid for step responses (p rows x m cols).

        Each subplot shows the step response from input j to output i.
        Open-loop traces are solid blue; closed-loop (when available)
        are solid green with dashed OL.

        Args:
            data: Computed data dict from _compute().

        Returns:
            Plotly-compatible plot dict.
        """
        step_data = data["step_data"]
        t = step_data["t"].tolist()
        responses = step_data["responses"]
        m = data["m"]
        p = data["p"]
        input_names = data["input_names"]
        output_names = data["output_names"]

        cl_step = data.get("cl_step_responses")
        has_cl = cl_step is not None

        traces: List[Dict] = []
        annotations: List[Dict] = []

        # Subplot grid positioning
        h_gap = 0.06
        v_gap = 0.06
        plot_w = (1.0 - h_gap * (m - 1)) / m if m > 1 else 1.0
        plot_h = (1.0 - v_gap * (p - 1)) / p if p > 1 else 1.0

        layout: Dict[str, Any] = {
            "paper_bgcolor": "#0a0e27",
            "plot_bgcolor": "#131b2e",
            "font": {"family": "Inter, sans-serif", "size": 11, "color": "#f1f5f9"},
            "margin": {"t": 50, "r": 25, "b": 55, "l": 60},
            "showlegend": has_cl,
            "legend": {
                "x": 0.01,
                "y": 0.99,
                "bgcolor": "rgba(19,27,46,0.8)",
                "font": {"size": 10, "color": "#94a3b8"},
            },
        }

        axis_idx = 1
        for i in range(p):  # rows = outputs
            for j in range(m):  # cols = inputs
                # Domain for this subplot
                x0 = j * (plot_w + h_gap)
                x1 = x0 + plot_w
                # Top-to-bottom: output 0 at top
                y1 = 1.0 - i * (plot_h + v_gap)
                y0 = y1 - plot_h

                x_key = "xaxis" if axis_idx == 1 else f"xaxis{axis_idx}"
                y_key = "yaxis" if axis_idx == 1 else f"yaxis{axis_idx}"
                xref = "x" if axis_idx == 1 else f"x{axis_idx}"
                yref = "y" if axis_idx == 1 else f"y{axis_idx}"

                layout[x_key] = {
                    "domain": [x0, x1],
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "showticklabels": i == p - 1,  # only bottom row
                    "title": {
                        "text": "Time (s)" if i == p - 1 else "",
                        "font": {"size": 10},
                    },
                }
                layout[y_key] = {
                    "domain": [y0, y1],
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                }

                # Column header (input name) — only top row
                if i == 0:
                    annotations.append({
                        "text": f"<b>{input_names[j] if j < len(input_names) else f'u{j+1}'}</b>",
                        "xref": "paper",
                        "yref": "paper",
                        "x": (x0 + x1) / 2,
                        "y": y1 + 0.02,
                        "showarrow": False,
                        "font": {"size": 11, "color": "#94a3b8"},
                    })

                # Row label (output name) — only first column
                if j == 0:
                    annotations.append({
                        "text": f"<b>{output_names[i] if i < len(output_names) else f'y{i+1}'}</b>",
                        "xref": "paper",
                        "yref": "paper",
                        "x": x0 - 0.03,
                        "y": (y0 + y1) / 2,
                        "showarrow": False,
                        "font": {"size": 11, "color": "#94a3b8"},
                        "textangle": -90,
                    })

                # Response trace
                key = (j, i)
                if key in responses:
                    y_data = responses[key]
                    if hasattr(y_data, "tolist"):
                        y_data = y_data.tolist()

                    if has_cl and key in cl_step:
                        # OL as dashed
                        traces.append({
                            "x": t,
                            "y": y_data,
                            "type": "scatter",
                            "mode": "lines",
                            "line": {"color": "#3b82f6", "width": 1.5, "dash": "dash"},
                            "xaxis": xref,
                            "yaxis": yref,
                            "name": "Open-Loop",
                            "showlegend": (i == 0 and j == 0),
                            "legendgroup": "ol",
                        })
                        # CL as solid
                        cl_y = cl_step[key]
                        if hasattr(cl_y, "tolist"):
                            cl_y = cl_y.tolist()
                        traces.append({
                            "x": t,
                            "y": cl_y,
                            "type": "scatter",
                            "mode": "lines",
                            "line": {"color": "#10b981", "width": 2},
                            "xaxis": xref,
                            "yaxis": yref,
                            "name": "Closed-Loop",
                            "showlegend": (i == 0 and j == 0),
                            "legendgroup": "cl",
                        })
                    else:
                        traces.append({
                            "x": t,
                            "y": y_data,
                            "type": "scatter",
                            "mode": "lines",
                            "line": {"color": "#3b82f6", "width": 2},
                            "xaxis": xref,
                            "yaxis": yref,
                            "showlegend": False,
                        })

                axis_idx += 1

        layout["annotations"] = annotations
        ts = time.time()
        layout["datarevision"] = f"step_grid-{ts}"
        layout["uirevision"] = "step_grid"

        return {
            "id": "step_response_grid",
            "title": "Step Response Grid",
            "data": traces,
            "layout": layout,
        }

    def _impulse_response_grid_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Plotly subplot grid for impulse responses (p rows x m cols).

        Same structure as step grid but for impulse data.

        Args:
            data: Computed data dict from _compute().

        Returns:
            Plotly-compatible plot dict.
        """
        impulse_data = data["impulse_data"]
        t = impulse_data["t"].tolist()
        responses = impulse_data["responses"]
        m = data["m"]
        p = data["p"]
        input_names = data["input_names"]
        output_names = data["output_names"]

        cl_impulse = data.get("cl_impulse_responses")
        has_cl = cl_impulse is not None

        traces: List[Dict] = []
        annotations: List[Dict] = []

        h_gap = 0.06
        v_gap = 0.06
        plot_w = (1.0 - h_gap * (m - 1)) / m if m > 1 else 1.0
        plot_h = (1.0 - v_gap * (p - 1)) / p if p > 1 else 1.0

        layout: Dict[str, Any] = {
            "paper_bgcolor": "#0a0e27",
            "plot_bgcolor": "#131b2e",
            "font": {"family": "Inter, sans-serif", "size": 11, "color": "#f1f5f9"},
            "margin": {"t": 50, "r": 25, "b": 55, "l": 60},
            "showlegend": has_cl,
            "legend": {
                "x": 0.01,
                "y": 0.99,
                "bgcolor": "rgba(19,27,46,0.8)",
                "font": {"size": 10, "color": "#94a3b8"},
            },
        }

        axis_idx = 1
        for i in range(p):
            for j in range(m):
                x0 = j * (plot_w + h_gap)
                x1 = x0 + plot_w
                y1 = 1.0 - i * (plot_h + v_gap)
                y0 = y1 - plot_h

                x_key = "xaxis" if axis_idx == 1 else f"xaxis{axis_idx}"
                y_key = "yaxis" if axis_idx == 1 else f"yaxis{axis_idx}"
                xref = "x" if axis_idx == 1 else f"x{axis_idx}"
                yref = "y" if axis_idx == 1 else f"y{axis_idx}"

                layout[x_key] = {
                    "domain": [x0, x1],
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                    "showticklabels": i == p - 1,
                    "title": {
                        "text": "Time (s)" if i == p - 1 else "",
                        "font": {"size": 10},
                    },
                }
                layout[y_key] = {
                    "domain": [y0, y1],
                    "gridcolor": "rgba(148,163,184,0.1)",
                    "zerolinecolor": "rgba(148,163,184,0.3)",
                }

                if i == 0:
                    annotations.append({
                        "text": f"<b>{input_names[j] if j < len(input_names) else f'u{j+1}'}</b>",
                        "xref": "paper",
                        "yref": "paper",
                        "x": (x0 + x1) / 2,
                        "y": y1 + 0.02,
                        "showarrow": False,
                        "font": {"size": 11, "color": "#94a3b8"},
                    })

                if j == 0:
                    annotations.append({
                        "text": f"<b>{output_names[i] if i < len(output_names) else f'y{i+1}'}</b>",
                        "xref": "paper",
                        "yref": "paper",
                        "x": x0 - 0.03,
                        "y": (y0 + y1) / 2,
                        "showarrow": False,
                        "font": {"size": 11, "color": "#94a3b8"},
                        "textangle": -90,
                    })

                key = (j, i)
                if key in responses:
                    y_data = responses[key]
                    if hasattr(y_data, "tolist"):
                        y_data = y_data.tolist()

                    if has_cl and key in cl_impulse:
                        traces.append({
                            "x": t,
                            "y": y_data,
                            "type": "scatter",
                            "mode": "lines",
                            "line": {"color": "#ef4444", "width": 1.5, "dash": "dash"},
                            "xaxis": xref,
                            "yaxis": yref,
                            "name": "Open-Loop",
                            "showlegend": (i == 0 and j == 0),
                            "legendgroup": "ol",
                        })
                        cl_y = cl_impulse[key]
                        if hasattr(cl_y, "tolist"):
                            cl_y = cl_y.tolist()
                        traces.append({
                            "x": t,
                            "y": cl_y,
                            "type": "scatter",
                            "mode": "lines",
                            "line": {"color": "#10b981", "width": 2},
                            "xaxis": xref,
                            "yaxis": yref,
                            "name": "Closed-Loop",
                            "showlegend": (i == 0 and j == 0),
                            "legendgroup": "cl",
                        })
                    else:
                        traces.append({
                            "x": t,
                            "y": y_data,
                            "type": "scatter",
                            "mode": "lines",
                            "line": {"color": "#ef4444", "width": 2},
                            "xaxis": xref,
                            "yaxis": yref,
                            "showlegend": False,
                        })

                axis_idx += 1

        layout["annotations"] = annotations
        ts = time.time()
        layout["datarevision"] = f"impulse_grid-{ts}"
        layout["uirevision"] = "impulse_grid"

        return {
            "id": "impulse_response_grid",
            "title": "Impulse Response Grid",
            "data": traces,
            "layout": layout,
        }

    def _eigenvalue_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build eigenvalue plot in the complex s-plane.

        Open-loop eigenvalues as red x markers. Closed-loop (when
        available) as green circle markers. Stable/unstable half-plane
        shading.

        Args:
            data: Computed data dict from _compute().

        Returns:
            Plotly-compatible plot dict.
        """
        eigs = data["eigenvalues"]
        re = eigs.real
        im = eigs.imag

        traces: List[Dict] = []

        # Compute axis range with padding
        all_re = list(re)
        all_im = list(im)
        cl_eigs = data.get("cl_eigenvalues")
        if cl_eigs is not None:
            all_re.extend(cl_eigs.real.tolist())
            all_im.extend(cl_eigs.imag.tolist())

        max_abs_re = max(abs(r) for r in all_re) if all_re else 1.0
        max_abs_im = max(abs(i) for i in all_im) if all_im else 1.0
        span = max(max_abs_re, max_abs_im, 0.5) * 1.4

        # Unstable half-plane shading (Re > 0)
        traces.append({
            "x": [0, span, span, 0],
            "y": [-span, -span, span, span],
            "type": "scatter",
            "mode": "none",
            "fill": "toself",
            "fillcolor": "rgba(239,68,68,0.05)",
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Stable half-plane shading (Re < 0)
        traces.append({
            "x": [0, -span, -span, 0],
            "y": [-span, -span, span, span],
            "type": "scatter",
            "mode": "none",
            "fill": "toself",
            "fillcolor": "rgba(16,185,129,0.05)",
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Axes lines
        traces.append({
            "x": [-span, span],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1},
            "showlegend": False,
            "hoverinfo": "skip",
        })
        traces.append({
            "x": [0, 0],
            "y": [-span, span],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": "rgba(148,163,184,0.3)", "width": 1},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Open-loop eigenvalues
        hover_ol = [
            f"\u03bb = {r:.4f} {'+' if i >= 0 else '-'} {abs(i):.4f}j"
            for r, i in zip(re, im)
        ]
        traces.append({
            "x": re.tolist(),
            "y": im.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {
                "symbol": "x",
                "size": 12,
                "color": "#ef4444",
                "line": {"width": 2, "color": "#ef4444"},
            },
            "name": "Open-Loop Poles",
            "text": hover_ol,
            "hoverinfo": "text",
        })

        # Closed-loop eigenvalues (if available)
        if cl_eigs is not None:
            cl_re = cl_eigs.real
            cl_im = cl_eigs.imag
            hover_cl = [
                f"\u03bb_cl = {r:.4f} {'+' if i >= 0 else '-'} {abs(i):.4f}j"
                for r, i in zip(cl_re, cl_im)
            ]
            traces.append({
                "x": cl_re.tolist(),
                "y": cl_im.tolist(),
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "circle",
                    "size": 10,
                    "color": "#10b981",
                    "line": {"width": 2, "color": "#10b981"},
                },
                "name": "Closed-Loop Poles",
                "text": hover_cl,
                "hoverinfo": "text",
            })

        ts = time.time()
        layout = {
            "paper_bgcolor": "#0a0e27",
            "plot_bgcolor": "#131b2e",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "xaxis": {
                "title": {"text": "Real", "font": {"size": 12}},
                "range": [-span, span],
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "yaxis": {
                "title": {"text": "Imaginary", "font": {"size": 12}},
                "range": [-span, span],
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "showlegend": True,
            "legend": {
                "x": 0.01,
                "y": 0.99,
                "bgcolor": "rgba(19,27,46,0.8)",
                "font": {"size": 10, "color": "#94a3b8"},
            },
            "datarevision": f"eigenvalues-{ts}",
            "uirevision": "eigenvalues",
        }

        return {
            "id": "eigenvalue_plot",
            "title": "Eigenvalue Map (s-plane)",
            "data": traces,
            "layout": layout,
        }

    # ------------------------------------------------------------------ #
    #  Plot assembly                                                     #
    # ------------------------------------------------------------------ #

    def _build_plots(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assemble all plots from computed data.

        Args:
            data: Computed data dict from _compute().

        Returns:
            List of Plotly plot dicts.
        """
        if data.get("error"):
            return []

        return [
            self._step_response_grid_plot(data),
            self._impulse_response_grid_plot(data),
            self._eigenvalue_plot(data),
        ]

    # ------------------------------------------------------------------ #
    #  Public interface                                                   #
    # ------------------------------------------------------------------ #

    def get_plots(self) -> List[Dict[str, Any]]:
        """Return plots (used by base class API; get_state overrides).

        Returns:
            List of Plotly plot dicts.
        """
        data = self._compute()
        return self._build_plots(data)

    def get_state(self) -> Dict[str, Any]:
        """Compute once and build metadata + plots from the same result.

        Returns:
            Full simulation state dict with parameters, plots, metadata.
        """
        data = self._compute()
        error = data.get("error")

        if error:
            return {
                "parameters": self.parameters.copy(),
                "plots": [],
                "metadata": {
                    "simulation_type": "mimo_design_studio",
                    "error": error,
                    "design_mode": self.parameters.get("design_mode", "analysis"),
                    "controller": {},
                },
            }

        eigs = data["eigenvalues"]
        n = data["n"]
        m = data["m"]
        p = data["p"]

        preset_id = data["preset_id"]
        preset_name = data["preset_name"]

        return {
            "parameters": self.parameters.copy(),
            "plots": self._build_plots(data),
            "metadata": {
                "simulation_type": "mimo_design_studio",
                "n_states": n,
                "n_inputs": m,
                "n_outputs": p,
                "preset": preset_id,
                "preset_name": preset_name,
                "matrices": {
                    "A": data["A"].tolist(),
                    "B": data["B"].tolist(),
                    "C": data["C"].tolist(),
                    "D": data["D"].tolist(),
                },
                "eigenvalues": {
                    "real": eigs.real.tolist(),
                    "imag": eigs.imag.tolist(),
                },
                "is_stable": data["is_stable"],
                "is_marginal": data["is_marginal"],
                "controllability_rank": data["ctrl_rank"],
                "observability_rank": data["obs_rank"],
                "is_controllable": bool(data["ctrl_rank"] == n),
                "is_observable": bool(data["obs_rank"] == n),
                "design_mode": self.parameters.get("design_mode", "analysis"),
                "controller": {},  # placeholder for Task 3
                "error": None,
                "state_names": data["state_names"],
                "input_names": data["input_names"],
                "output_names": data["output_names"],
            },
        }
