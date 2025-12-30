"""
Data Handler - Converts simulation outputs to JSON-serializable formats.

Handles:
- NumPy arrays -> Python lists
- Complex numbers -> {"real": ..., "imag": ...}
- Matplotlib figures -> Plotly JSON format
- NumPy numeric types -> Python native types
- SciPy sparse matrices -> dense arrays
- Datetime objects -> ISO strings
"""

import json
from typing import Any, Dict, List, Optional, Union
import numbers
from datetime import datetime, date


class DataHandler:
    """
    Handles conversion of simulation data to JSON-serializable formats.

    Supports:
    - NumPy arrays -> Python lists
    - Complex numbers -> {"real": ..., "imag": ...}
    - Matplotlib figures -> Plotly JSON format
    - NumPy numeric types -> Python native types
    - SciPy sparse matrices -> dense arrays
    - Datetime objects -> ISO strings
    """

    @staticmethod
    def is_numpy_available() -> bool:
        """Check if numpy is available."""
        try:
            import numpy
            return True
        except ImportError:
            return False

    @staticmethod
    def is_matplotlib_available() -> bool:
        """Check if matplotlib is available."""
        try:
            import matplotlib
            return True
        except ImportError:
            return False

    @staticmethod
    def is_scipy_available() -> bool:
        """Check if scipy is available."""
        try:
            import scipy
            return True
        except ImportError:
            return False

    @classmethod
    def complex_to_dict(cls, value: Any) -> Union[Dict[str, float], List[Dict[str, float]], Any]:
        """
        Convert complex number(s) to dictionary format.

        Args:
            value: Complex number, numpy array of complex, or other value

        Returns:
            For complex: {"real": float, "imag": float}
            For array: List of dicts
            Otherwise: unchanged value
        """
        if cls.is_numpy_available():
            import numpy as np

            # Handle numpy complex types
            if isinstance(value, (np.complexfloating, complex)):
                return {"real": float(value.real), "imag": float(value.imag)}

            # Handle numpy array of complex
            if isinstance(value, np.ndarray) and np.iscomplexobj(value):
                flat = value.flatten()
                return [{"real": float(v.real), "imag": float(v.imag)} for v in flat]

        # Handle Python complex
        if isinstance(value, complex):
            return {"real": float(value.real), "imag": float(value.imag)}

        return value

    @classmethod
    def array_to_json(cls, arr: Any) -> Union[List, Dict, Any]:
        """
        Convert a numpy array to JSON-serializable format.

        Args:
            arr: numpy array or array-like object

        Returns:
            List (for 1D), List of lists (for 2D+), or dict for complex
        """
        if cls.is_numpy_available():
            import numpy as np

            if isinstance(arr, np.ndarray):
                # Handle complex arrays specially
                if np.iscomplexobj(arr):
                    return cls.complex_to_dict(arr)

                # Convert to nested Python lists
                return arr.tolist()

        # Handle other iterables
        if hasattr(arr, 'tolist'):
            return arr.tolist()

        if hasattr(arr, '__iter__') and not isinstance(arr, (str, dict)):
            return list(arr)

        return arr

    @classmethod
    def array_to_list(cls, arr: Any) -> List:
        """
        Convert a numpy array to a Python list.

        Args:
            arr: numpy array or array-like object

        Returns:
            Python list
        """
        if cls.is_numpy_available():
            import numpy as np
            if isinstance(arr, np.ndarray):
                return arr.tolist()

        # Handle other iterables
        if hasattr(arr, 'tolist'):
            return arr.tolist()

        if hasattr(arr, '__iter__') and not isinstance(arr, (str, dict)):
            return list(arr)

        return [arr]

    @classmethod
    def convert_numeric(cls, value: Any) -> Union[int, float, Any]:
        """
        Convert numpy numeric types to Python native types.

        Args:
            value: Any value, possibly numpy numeric type

        Returns:
            Python native type if numeric, otherwise unchanged
        """
        if cls.is_numpy_available():
            import numpy as np

            if isinstance(value, (np.integer, np.int64, np.int32)):
                return int(value)
            if isinstance(value, (np.floating, np.float64, np.float32)):
                return float(value)
            if isinstance(value, np.bool_):
                return bool(value)
            if isinstance(value, np.ndarray):
                return cls.array_to_list(value)

        if isinstance(value, numbers.Integral):
            return int(value)
        if isinstance(value, numbers.Real):
            return float(value)

        return value

    @classmethod
    def serialize_result(cls, data: Any) -> Any:
        """
        Recursively serialize data to JSON-compatible format.

        Args:
            data: Any data structure (dict, list, numpy array, etc.)

        Returns:
            JSON-serializable data structure

        Handles:
        - None -> null
        - str, bool -> unchanged
        - numbers -> Python int/float
        - complex -> {"real": ..., "imag": ...}
        - datetime -> ISO string
        - numpy arrays -> lists
        - scipy sparse matrices -> dense arrays -> lists
        - dicts -> recursively serialized
        - lists/tuples -> recursively serialized
        """
        if data is None:
            return None

        if isinstance(data, (str, bool)):
            return data

        # Handle complex numbers (Python built-in)
        if isinstance(data, complex):
            return cls.complex_to_dict(data)

        # Handle datetime objects
        if isinstance(data, datetime):
            return data.isoformat()

        if isinstance(data, date):
            return data.isoformat()

        # Handle regular numbers (after complex check)
        if isinstance(data, numbers.Number):
            return cls.convert_numeric(data)

        if isinstance(data, dict):
            return {
                str(key): cls.serialize_result(value)
                for key, value in data.items()
            }

        if isinstance(data, (list, tuple)):
            return [cls.serialize_result(item) for item in data]

        # Handle numpy arrays and types
        if cls.is_numpy_available():
            import numpy as np

            # Handle numpy complex types
            if isinstance(data, np.complexfloating):
                return cls.complex_to_dict(data)

            # Handle numpy arrays
            if isinstance(data, np.ndarray):
                # Complex arrays
                if np.iscomplexobj(data):
                    # Return as list of dicts for multi-element, or single dict
                    if data.size == 1:
                        return cls.complex_to_dict(data.item())
                    return [cls.serialize_result(x) for x in data.flatten()]

                # Regular arrays - convert to nested list
                return cls.array_to_list(data)

        # Handle scipy sparse matrices
        if cls.is_scipy_available():
            try:
                from scipy import sparse
                if sparse.issparse(data):
                    # Convert sparse to dense, then to list
                    dense = data.toarray()
                    return cls.serialize_result(dense)
            except Exception:
                pass

        # Handle scipy TransferFunction or similar objects
        if hasattr(data, 'num') and hasattr(data, 'den'):
            return {
                "num": cls.serialize_result(getattr(data, 'num', None)),
                "den": cls.serialize_result(getattr(data, 'den', None)),
            }

        # Handle objects with __dict__
        if hasattr(data, '__dict__'):
            return cls.serialize_result(data.__dict__)

        # Last resort: try to convert to string
        try:
            return str(data)
        except Exception:
            return None

    @classmethod
    def figure_to_plotly(cls, fig: Any) -> Dict[str, Any]:
        """
        Convert a matplotlib figure to Plotly JSON format.

        Args:
            fig: matplotlib Figure object

        Returns:
            Dict in Plotly format with 'data' and 'layout' keys
        """
        if not cls.is_matplotlib_available():
            return {
                "data": [],
                "layout": {"title": "Matplotlib not available"}
            }

        try:
            import matplotlib.pyplot as plt

            plotly_data = []
            layout = {
                "title": "",
                "xaxis": {"title": ""},
                "yaxis": {"title": ""},
            }

            # Get all axes from the figure
            for ax in fig.get_axes():
                # Extract axis labels
                if ax.get_xlabel():
                    layout["xaxis"]["title"] = ax.get_xlabel()
                if ax.get_ylabel():
                    layout["yaxis"]["title"] = ax.get_ylabel()
                if ax.get_title():
                    layout["title"] = ax.get_title()

                # Extract line plots
                for line in ax.get_lines():
                    xdata = line.get_xdata()
                    ydata = line.get_ydata()

                    trace = {
                        "x": cls.array_to_list(xdata),
                        "y": cls.array_to_list(ydata),
                        "type": "scatter",
                        "mode": "lines",
                        "name": line.get_label() if line.get_label() and not line.get_label().startswith('_') else "",
                        "line": {
                            "color": line.get_color() if isinstance(line.get_color(), str) else None,
                            "width": line.get_linewidth(),
                        }
                    }
                    plotly_data.append(trace)

                # Extract scatter plots (collections)
                for collection in ax.collections:
                    if hasattr(collection, 'get_offsets'):
                        offsets = collection.get_offsets()
                        if len(offsets) > 0:
                            trace = {
                                "x": cls.array_to_list(offsets[:, 0]),
                                "y": cls.array_to_list(offsets[:, 1]),
                                "type": "scatter",
                                "mode": "markers",
                                "name": "",
                            }
                            plotly_data.append(trace)

            return {
                "data": plotly_data,
                "layout": layout,
            }

        except Exception as e:
            return {
                "data": [],
                "layout": {"title": f"Conversion error: {str(e)}"}
            }

    @classmethod
    def subsample_data(
        cls,
        x: List,
        y: List,
        max_points: int = 1000,
        preserve_peaks: bool = True,
    ) -> tuple:
        """
        Subsample large datasets to reduce bandwidth while preserving signal shape.

        Uses intelligent subsampling that preserves peaks and valleys for better
        visual representation of the original signal.

        Args:
            x: X-axis data (list or numpy array)
            y: Y-axis data (list or numpy array)
            max_points: Maximum number of points to return (default 1000)
            preserve_peaks: If True, use LTTB-like algorithm to preserve peaks

        Returns:
            Tuple of (subsampled_x, subsampled_y)
        """
        if cls.is_numpy_available():
            import numpy as np

            # Convert to numpy arrays if needed
            x_arr = np.asarray(x)
            y_arr = np.asarray(y)

            n_points = len(x_arr)

            # No subsampling needed if already under limit
            if n_points <= max_points:
                return x_arr.tolist(), y_arr.tolist()

            if preserve_peaks:
                # Largest-Triangle-Three-Buckets (LTTB) inspired algorithm
                # Simplified version that preserves min/max in each bucket
                bucket_size = n_points / max_points
                sampled_x = [x_arr[0]]
                sampled_y = [y_arr[0]]

                for i in range(max_points - 2):
                    start = int(i * bucket_size) + 1
                    end = int((i + 1) * bucket_size) + 1
                    end = min(end, n_points - 1)

                    if start >= end:
                        continue

                    bucket_y = y_arr[start:end]
                    bucket_x = x_arr[start:end]

                    # Find index of value furthest from line between neighbors
                    # Simplified: just pick the point with max absolute value in bucket
                    max_idx = np.argmax(np.abs(bucket_y - np.mean(bucket_y)))
                    sampled_x.append(bucket_x[max_idx])
                    sampled_y.append(bucket_y[max_idx])

                # Always include last point
                sampled_x.append(x_arr[-1])
                sampled_y.append(y_arr[-1])

                return sampled_x, sampled_y
            else:
                # Simple uniform subsampling
                indices = np.linspace(0, n_points - 1, max_points, dtype=int)
                return x_arr[indices].tolist(), y_arr[indices].tolist()

        # Fallback for no numpy
        n_points = len(x)
        if n_points <= max_points:
            return list(x), list(y)

        step = n_points // max_points
        indices = range(0, n_points, step)
        return [x[i] for i in indices], [y[i] for i in indices]

    @classmethod
    def create_plotly_trace(
        cls,
        x: List,
        y: List,
        name: str = "",
        mode: str = "lines",
        line_color: Optional[str] = None,
        line_width: float = 2,
        marker_size: int = 8,
        marker_color: Optional[str] = None,
        max_points: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a Plotly trace dictionary.

        Args:
            x: X-axis data
            y: Y-axis data
            name: Trace name for legend
            mode: 'lines', 'markers', or 'lines+markers'
            line_color: Color for lines
            line_width: Width for lines
            marker_size: Size for markers
            marker_color: Color for markers
            max_points: If > 0, subsample data to this many points for performance

        Returns:
            Plotly trace dictionary
        """
        # Apply subsampling if requested
        if max_points > 0 and len(x) > max_points:
            x, y = cls.subsample_data(x, y, max_points=max_points)

        trace = {
            "x": cls.serialize_result(x),
            "y": cls.serialize_result(y),
            "type": "scatter",
            "mode": mode,
            "name": name,
        }

        if "lines" in mode:
            trace["line"] = {
                "width": line_width,
            }
            if line_color:
                trace["line"]["color"] = line_color

        if "markers" in mode:
            trace["marker"] = {
                "size": marker_size,
            }
            if marker_color:
                trace["marker"]["color"] = marker_color

        return trace

    @classmethod
    def create_plotly_layout(
        cls,
        title: str = "",
        xaxis_title: str = "",
        yaxis_title: str = "",
        xaxis_type: Optional[str] = None,
        yaxis_type: Optional[str] = None,
        xaxis_range: Optional[List] = None,
        yaxis_range: Optional[List] = None,
        showlegend: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a Plotly layout dictionary.

        Args:
            title: Plot title
            xaxis_title: X-axis label
            yaxis_title: Y-axis label
            xaxis_type: 'linear', 'log', etc.
            yaxis_type: 'linear', 'log', etc.
            xaxis_range: [min, max] for x-axis
            yaxis_range: [min, max] for y-axis
            showlegend: Whether to show legend

        Returns:
            Plotly layout dictionary
        """
        layout = {
            "title": {"text": title},
            "xaxis": {"title": xaxis_title},
            "yaxis": {"title": yaxis_title},
            "showlegend": showlegend,
        }

        if xaxis_type:
            layout["xaxis"]["type"] = xaxis_type
        if yaxis_type:
            layout["yaxis"]["type"] = yaxis_type
        if xaxis_range:
            layout["xaxis"]["range"] = xaxis_range
        if yaxis_range:
            layout["yaxis"]["range"] = yaxis_range

        return layout


# Convenience instance
data_handler = DataHandler()
