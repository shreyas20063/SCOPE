"""
Simulation Executor - Handles safe execution of simulation code.
"""

import signal
import traceback
from typing import Any, Dict, Optional, Callable
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


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

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_workers: int = 4):
        """
        Initialize the executor.

        Args:
            timeout: Maximum execution time in seconds (default: 30)
            max_workers: Thread pool size (default: 4)
        """
        self.timeout = min(timeout, 60)  # Cap at 60 seconds max
        self._sim_locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()  # Protects _sim_locks dict
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def _get_lock(self, sim_id: Optional[str] = None, func: Optional[Callable] = None) -> threading.Lock:
        """Get a per-(sim, simulator-instance) lock.

        When `func` is a bound method (e.g. `simulator.get_state`), we key the
        lock by `(sim_id, id(func.__self__))` — i.e. the Python id of the
        simulator INSTANCE. Since main.py keeps one simulator instance per
        (sim_id, session_id) in its `active_simulators` dict, this gives each
        session its own lock automatically — without the caller having to
        thread session_id through 21 call sites.

        Two sessions on the same sim_id get different instances → different
        locks → can compute in parallel. Same session calling repeatedly gets
        the same instance → same lock → still serialized (which is correct,
        since the simulator's internal state isn't thread-safe).

        Memory note: `id()` values can be reused after GC, but main.py's
        idle-cleanup only drops active_simulators entries after 30 min — by
        which time any stale lock under that id is irrelevant. Lock dict
        growth is bounded by live simulator instances in practice.
        """
        if func is not None and hasattr(func, '__self__'):
            key = f"{sim_id or ''}::{id(func.__self__)}"
        elif sim_id:
            key = sim_id
        else:
            key = "__default__"
        with self._locks_lock:
            if key not in self._sim_locks:
                self._sim_locks[key] = threading.Lock()
            return self._sim_locks[key]

    def execute(
        self,
        func: Callable,
        *args,
        sim_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a function with timeout protection and error handling.

        Args:
            func: The function to execute. If it's a bound method, the lock
                  is automatically keyed by `(sim_id, id(func.__self__))` so
                  two sessions on the same simulation don't serialize.
            *args: Positional arguments for the function
            sim_id: Optional simulator ID. Used as the lock key prefix.
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

        lock = self._get_lock(sim_id, func)
        with lock:
            try:
                future = self._pool.submit(func, *args, **kwargs)
                try:
                    result["data"] = future.result(timeout=self.timeout)
                    result["success"] = True
                except FuturesTimeoutError:
                    future.cancel()
                    result["error"] = f"Execution timed out after {self.timeout} seconds"
                    result["details"] = "The simulation took too long to complete. Try with simpler parameters."

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


