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

    # Hub integration — override in subclasses
    HUB_SLOTS: List[str] = []
    HUB_DOMAIN: str = "ct"  # "ct" or "dt"
    HUB_DIMENSIONS: Dict[str, Any] = {"n": None, "m": 1, "p": 1}  # SISO default

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
        self.initialize()
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

    def to_hub_data(self) -> Optional[Dict[str, Any]]:
        """Serialize this sim's state for pushing to the hub.

        Default: export TF from common parameter name patterns.
        Override for sims with non-standard parameter names.
        """
        num = den = None
        for key in ('numerator', 'num_coeffs', 'custom_num', 'plant_num', 'tf_numerator'):
            if key in self.parameters:
                val = self.parameters[key]
                num = self._parse_coeffs(val) if isinstance(val, str) else val
                break
        for key in ('denominator', 'den_coeffs', 'custom_den', 'plant_den', 'tf_denominator'):
            if key in self.parameters:
                val = self.parameters[key]
                den = self._parse_coeffs(val) if isinstance(val, str) else val
                break

        if num is not None and den is not None:
            return {
                "source": "tf",
                "domain": self.HUB_DOMAIN,
                "dimensions": self.HUB_DIMENSIONS,
                "tf": {
                    "num": list(num) if hasattr(num, '__iter__') else [num],
                    "den": list(den) if hasattr(den, '__iter__') else [den],
                    "variable": "z" if self.HUB_DOMAIN == "dt" else "s",
                },
            }
        return None

    def from_hub_data(self, hub_data: Dict[str, Any]) -> bool:
        """Load hub data into this sim's parameters.

        Default: inject TF num/den into common parameter names.
        Returns True if data was applicable.
        """
        if not hub_data:
            return False

        # SISO/MIMO compatibility
        dims = hub_data.get("dimensions", {})
        if self.HUB_DIMENSIONS.get("m", 1) == 1 and self.HUB_DIMENSIONS.get("p", 1) == 1:
            if dims.get("m", 1) != 1 or dims.get("p", 1) != 1:
                return False

        # Domain compatibility
        domain = hub_data.get("domain", "ct")
        if domain != self.HUB_DOMAIN:
            return False

        tf = hub_data.get("tf")
        if tf and tf.get("num") and tf.get("den"):
            num_str = ", ".join(str(c) for c in tf["num"])
            den_str = ", ".join(str(c) for c in tf["den"])
            for key in ('numerator', 'num_coeffs', 'custom_num', 'plant_num', 'tf_numerator'):
                if key in self.PARAMETER_SCHEMA:
                    self.parameters[key] = num_str
                    break
            for key in ('denominator', 'den_coeffs', 'custom_den', 'plant_den', 'tf_denominator'):
                if key in self.PARAMETER_SCHEMA:
                    self.parameters[key] = den_str
                    break
            return True

        return False

    @staticmethod
    def _parse_coeffs(val: str) -> List[float]:
        """Parse comma-separated coefficient string to float list."""
        try:
            return [float(x.strip()) for x in str(val).split(',') if x.strip()]
        except (ValueError, AttributeError):
            return []
