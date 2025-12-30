# Simulations package
"""
Simulation module with registry system.

To add a new simulator:
1. Create a new class extending BaseSimulator
2. Register it in SIMULATOR_REGISTRY with its catalog ID
3. Add the simulation to catalog.py with has_simulator=True
"""

from .base_simulator import BaseSimulator
from .rc_lowpass_filter import RCLowpassSimulator
from .fourier_series import FourierSeriesSimulator
from .second_order_system import SecondOrderSystemSimulator
from .convolution_simulator import ConvolutionSimulator
from .aliasing_quantization import AliasingQuantizationSimulator
from .fourier_phase_vs_magnitude import FourierPhaseMagnitudeSimulator
from .modulation_techniques import ModulationTechniquesSimulator
from .ct_dt_poles import CTDTPolesSimulator
from .dc_motor import DCMotorSimulator
from .feedback_system_analysis import FeedbackAmplifierSimulator
from .amplifier_topologies import AmplifierSimulator
from .lens_optics import LensOpticsSimulator
from .furuta_pendulum import FurutaPendulumSimulator

# Registry mapping simulation IDs to their simulator classes
# Add new simulators here as they are implemented
SIMULATOR_REGISTRY = {
    "rc_lowpass_filter": RCLowpassSimulator,
    "fourier_series": FourierSeriesSimulator,
    "second_order_system": SecondOrderSystemSimulator,
    "convolution_simulator": ConvolutionSimulator,
    "aliasing_quantization": AliasingQuantizationSimulator,
    "fourier_phase_vs_magnitude": FourierPhaseMagnitudeSimulator,
    "modulation_techniques": ModulationTechniquesSimulator,
    "ct_dt_poles": CTDTPolesSimulator,
    "dc_motor": DCMotorSimulator,
    "feedback_system_analysis": FeedbackAmplifierSimulator,
    "amplifier_topologies": AmplifierSimulator,
    "lens_optics": LensOpticsSimulator,
    "furuta_pendulum": FurutaPendulumSimulator,
}


def get_simulator_class(sim_id: str):
    """
    Get simulator class by simulation ID.

    Args:
        sim_id: The simulation ID from catalog.py

    Returns:
        The simulator class if registered, None otherwise
    """
    return SIMULATOR_REGISTRY.get(sim_id)


def is_simulator_available(sim_id: str) -> bool:
    """Check if a simulator is registered for the given ID."""
    return sim_id in SIMULATOR_REGISTRY


def get_registered_simulators():
    """Return list of all registered simulator IDs."""
    return list(SIMULATOR_REGISTRY.keys())


def register_simulator(sim_id: str, simulator_class: type):
    """
    Dynamically register a simulator class.

    Args:
        sim_id: The simulation ID (must match catalog.py)
        simulator_class: Class extending BaseSimulator
    """
    if not issubclass(simulator_class, BaseSimulator):
        raise TypeError(f"Simulator must extend BaseSimulator, got {type(simulator_class)}")
    SIMULATOR_REGISTRY[sim_id] = simulator_class


__all__ = [
    "BaseSimulator",
    "RCLowpassSimulator",
    "FourierSeriesSimulator",
    "SecondOrderSystemSimulator",
    "ConvolutionSimulator",
    "AliasingQuantizationSimulator",
    "FourierPhaseMagnitudeSimulator",
    "ModulationTechniquesSimulator",
    "CTDTPolesSimulator",
    "DCMotorSimulator",
    "FeedbackAmplifierSimulator",
    "AmplifierSimulator",
    "LensOpticsSimulator",
    "FurutaPendulumSimulator",
    "SIMULATOR_REGISTRY",
    "get_simulator_class",
    "is_simulator_available",
    "get_registered_simulators",
    "register_simulator",
]
