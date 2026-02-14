"""
Simulation Executor - Handles safe execution of simulation code.
"""

import signal
import traceback
from typing import Any, Dict, Optional, Callable
from functools import wraps
import threading


class ExecutionTimeout(Exception):
    """Raised when execution exceeds the timeout limit."""
    pass


class ExecutionError(Exception):
    """Raised when execution fails with an error."""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise ExecutionTimeout("Execution timed out")


class SimulationExecutor:
    """
    Executes simulation code safely with timeout protection and error handling.

    Usage:
        executor = SimulationExecutor(timeout=30)
        result = executor.execute(my_function, param1=value1, param2=value2)
    """

    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the executor.

        Args:
            timeout: Maximum execution time in seconds (default: 30)
        """
        self.timeout = min(timeout, 60)  # Cap at 60 seconds max
        self._lock = threading.Lock()

    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
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
                - error: str or None (error message if failed)
                - details: str or None (traceback if failed)
        """
        result = {
            "success": False,
            "data": None,
            "error": None,
            "details": None
        }

        with self._lock:
            try:
                # Set up timeout using threading (cross-platform)
                execution_result = [None]
                execution_error = [None]

                def target():
                    try:
                        execution_result[0] = func(*args, **kwargs)
                    except Exception as e:
                        execution_error[0] = e

                thread = threading.Thread(target=target)
                thread.start()
                thread.join(timeout=self.timeout)

                if thread.is_alive():
                    # Timeout occurred
                    result["error"] = f"Execution timed out after {self.timeout} seconds"
                    result["details"] = "The simulation took too long to complete. Try with simpler parameters."
                    return result

                if execution_error[0] is not None:
                    raise execution_error[0]

                result["success"] = True
                result["data"] = execution_result[0]

            except ExecutionTimeout as e:
                result["error"] = str(e)
                result["details"] = "The simulation took too long to complete."

            except ExecutionError as e:
                result["error"] = e.message
                result["details"] = e.details

            except TypeError as e:
                result["error"] = "Invalid parameters provided"
                result["details"] = str(e)

            except ValueError as e:
                result["error"] = "Invalid value in parameters"
                result["details"] = str(e)

            except Exception as e:
                result["error"] = f"Execution failed: {type(e).__name__}"
                result["details"] = traceback.format_exc()

        return result

    def execute_method(
        self,
        obj: Any,
        method_name: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a method on an object with timeout protection.

        Args:
            obj: The object containing the method
            method_name: Name of the method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Same format as execute()
        """
        if not hasattr(obj, method_name):
            return {
                "success": False,
                "data": None,
                "error": f"Method '{method_name}' not found",
                "details": None
            }

        method = getattr(obj, method_name)
        if not callable(method):
            return {
                "success": False,
                "data": None,
                "error": f"'{method_name}' is not callable",
                "details": None
            }

        return self.execute(method, *args, **kwargs)

    def validate_params(
        self,
        params: Dict[str, Any],
        schema: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Validate parameters against a schema.

        Args:
            params: Dictionary of parameter values
            schema: Dictionary defining parameter constraints
                    Each key maps to {"type": str, "min": num, "max": num, "options": list}

        Returns:
            Dict with validated/clamped values

        Raises:
            ValueError if required params are missing
        """
        validated = {}

        for name, constraints in schema.items():
            if name not in params:
                if "default" in constraints:
                    validated[name] = constraints["default"]
                    continue
                else:
                    raise ValueError(f"Missing required parameter: {name}")

            value = params[name]
            param_type = constraints.get("type", "number")

            if param_type in ("number", "slider"):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Parameter '{name}' must be a number")

                if "min" in constraints:
                    value = max(constraints["min"], value)
                if "max" in constraints:
                    value = min(constraints["max"], value)

            elif param_type == "select":
                options = constraints.get("options", [])
                valid_values = [opt["value"] if isinstance(opt, dict) else opt for opt in options]
                if value not in valid_values and valid_values:
                    value = valid_values[0]

            elif param_type == "checkbox":
                value = bool(value)

            validated[name] = value

        return validated


# Global executor instance with default timeout
default_executor = SimulationExecutor()
