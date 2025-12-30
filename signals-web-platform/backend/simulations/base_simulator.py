"""
Base Simulator - Abstract base class for all simulation implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseSimulator(ABC):
    """
    Abstract base class for all simulation implementations.

    Each simulation must implement:
    - initialize(params): Set up initial state with parameters
    - update_parameter(name, value): Update a single parameter
    - get_state(): Return current state as JSON
    - get_plots(): Return plots as list of Plotly dicts

    Subclasses should define:
    - PARAMETER_SCHEMA: Dict defining parameter constraints
    - DEFAULT_PARAMS: Dict of default parameter values
    """

    # Override these in subclasses
    PARAMETER_SCHEMA: Dict[str, Dict] = {}
    DEFAULT_PARAMS: Dict[str, Any] = {}

    def __init__(self, simulation_id: str):
        """
        Initialize base simulator.

        Args:
            simulation_id: Unique identifier for this simulation
        """
        self.simulation_id = simulation_id
        self.parameters: Dict[str, Any] = {}
        self._initialized = False

    @abstractmethod
    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the simulation with given or default parameters.

        Args:
            params: Optional parameter overrides
        """
        pass

    @abstractmethod
    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """
        Update a single parameter and return updated state.

        Args:
            name: Parameter name
            value: New parameter value

        Returns:
            Dict with 'parameters' and 'plots' keys
        """
        pass

    @abstractmethod
    def get_plots(self) -> List[Dict[str, Any]]:
        """
        Generate and return current plots.

        Returns:
            List of plot dictionaries, each with:
            - id: str (unique plot identifier)
            - title: str (plot title)
            - data: list (Plotly trace objects)
            - layout: dict (Plotly layout object)
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Return current simulation state.

        Returns:
            Dict with:
            - parameters: current parameter values
            - plots: list of Plotly plot dicts
        """
        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
        }

    def reset(self) -> Dict[str, Any]:
        """
        Reset simulation to default parameters.

        Returns:
            Updated state after reset
        """
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        return self.get_state()

    def run(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run simulation with given parameters.

        Args:
            params: Optional parameter values

        Returns:
            Simulation state with plots
        """
        if not self._initialized:
            self.initialize(params)
        elif params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)

        return self.get_state()

    def _validate_param(self, name: str, value: Any) -> Any:
        """
        Validate a parameter value against the schema.

        Args:
            name: Parameter name
            value: Parameter value

        Returns:
            Validated (possibly clamped) value
        """
        if name not in self.PARAMETER_SCHEMA:
            return value

        schema = self.PARAMETER_SCHEMA[name]
        param_type = schema.get("type", "number")

        if param_type in ("number", "slider"):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return schema.get("default", 0)

            if "min" in schema:
                value = max(schema["min"], value)
            if "max" in schema:
                value = min(schema["max"], value)

        elif param_type == "select":
            options = schema.get("options", [])
            valid_values = [
                opt["value"] if isinstance(opt, dict) else opt
                for opt in options
            ]
            if value not in valid_values and valid_values:
                value = valid_values[0]

        elif param_type == "checkbox":
            value = bool(value)

        return value

    def get_parameter_schema(self) -> Dict[str, Dict]:
        """Return the parameter schema for this simulation."""
        return self.PARAMETER_SCHEMA.copy()

    def get_default_params(self) -> Dict[str, Any]:
        """Return default parameter values."""
        return self.DEFAULT_PARAMS.copy()

    @property
    def is_initialized(self) -> bool:
        """Check if simulation has been initialized."""
        return self._initialized
