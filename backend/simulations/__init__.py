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
from .fundamental_modes import FundamentalModesSimulator
from .second_order_system import SecondOrderSystemSimulator
from .convolution_simulator import ConvolutionSimulator
from .aliasing_quantization import AliasingQuantizationSimulator
from .fourier_phase_vs_magnitude import FourierPhaseMagnitudeSimulator
from .modulation_techniques import ModulationTechniquesSimulator
from .ct_dt_poles import CTDTPolesSimulator
from .dc_motor import DCMotorSimulator
from .dt_difference_equation import DifferenceEquationSimulator
from .feedback_system_analysis import FeedbackAmplifierSimulator
from .amplifier_topologies import AmplifierSimulator
from .lens_optics import LensOpticsSimulator
from .furuta_pendulum import FurutaPendulumSimulator
from .block_diagram_builder import BlockDiagramSimulator
from .cyclic_path_detector import CyclicPathDetectorSimulator
from .feedback_convergence import FeedbackConvergenceSimulator
from .signal_operations import SignalOperationsSimulator
from .state_space_analyzer import StateSpaceAnalyzerSimulator
from .sampling_reconstruction import SamplingReconstructionSimulator
from .mass_spring_system import MassSpringSimulator
from .polynomial_multiplication import PolynomialMultiplicationSimulator
from .operator_algebra import OperatorAlgebraSimulator
from .pole_behavior import PoleBehaviorSimulator
from .cascade_parallel import CascadeParallelSimulator
from .dt_ct_comparator import DTCTComparatorSimulator
from .impulse_construction import ImpulseConstructionSimulator
from .ct_impulse_response import CTImpulseResponseSimulator
from .complex_poles_modes import ComplexPolesModesSimulator
from .z_transform_properties import ZTransformPropertiesSimulator
from .z_transform_roc import ZTransformROCSimulator
from .inverse_z_transform import InverseZTransformSimulator
from .dt_system_representations import SystemRepresentationSimulator
from .laplace_roc import LaplaceROCSimulator
from .laplace_properties import LaplacePropertiesSimulator
from .ivt_fvt_visualizer import IVTFVTSimulator
from .ode_laplace_solver import ODELaplaceSolverSimulator
from .resonance_anatomy import ResonanceAnatomySimulator
from .vector_freq_response import VectorFreqResponseSimulator
from .eigenfunction_tester import EigenfunctionTesterSimulator
from .audio_freq_response import AudioFreqResponseSimulator
from .delay_instability import DelayInstabilitySimulator
from .signal_flow_scope import SignalFlowScopeSimulator
from .nyquist_bode_comparison import NyquistBodeComparisonSimulator
from .root_locus import RootLocusSimulator
from .routh_hurwitz import RouthHurwitzSimulator
from .nyquist_stability import NyquistStabilitySimulator
from .controller_tuning_lab import ControllerTuningLabSimulator
from .lead_lag_designer import LeadLagDesignerSimulator
from .steady_state_error import SteadyStateErrorSimulator
from .phase_portrait import PhasePortraitSimulator
from .nonlinear_control_lab import NonlinearControlLabSimulator
from .mimo_design_studio import MIMODesignStudioSimulator
from .inverted_pendulum_3d import InvertedPendulum3DSimulator
from .ball_beam_3d import BallBeam3DSimulator
from .coupled_tanks_3d import CoupledTanks3DSimulator

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
    "dt_difference_equation": DifferenceEquationSimulator,
    "feedback_system_analysis": FeedbackAmplifierSimulator,
    "amplifier_topologies": AmplifierSimulator,
    "lens_optics": LensOpticsSimulator,
    "furuta_pendulum": FurutaPendulumSimulator,
    "block_diagram_builder": BlockDiagramSimulator,
    "cyclic_path_detector": CyclicPathDetectorSimulator,
    "feedback_convergence": FeedbackConvergenceSimulator,
    "fundamental_modes": FundamentalModesSimulator,
    "signal_operations": SignalOperationsSimulator,
    "state_space_analyzer": StateSpaceAnalyzerSimulator,
    "sampling_reconstruction": SamplingReconstructionSimulator,
    "mass_spring_system": MassSpringSimulator,
    "polynomial_multiplication": PolynomialMultiplicationSimulator,
    "operator_algebra": OperatorAlgebraSimulator,
    "pole_behavior": PoleBehaviorSimulator,
    "cascade_parallel": CascadeParallelSimulator,
    "dt_ct_comparator": DTCTComparatorSimulator,
    "impulse_construction": ImpulseConstructionSimulator,
    "ct_impulse_response": CTImpulseResponseSimulator,
    "complex_poles_modes": ComplexPolesModesSimulator,
    "z_transform_properties": ZTransformPropertiesSimulator,
    "z_transform_roc": ZTransformROCSimulator,
    "inverse_z_transform": InverseZTransformSimulator,
    "dt_system_representations": SystemRepresentationSimulator,
    "laplace_roc": LaplaceROCSimulator,
    "laplace_properties": LaplacePropertiesSimulator,
    "ivt_fvt_visualizer": IVTFVTSimulator,
    "ode_laplace_solver": ODELaplaceSolverSimulator,
    "resonance_anatomy": ResonanceAnatomySimulator,
    "vector_freq_response": VectorFreqResponseSimulator,
    "eigenfunction_tester": EigenfunctionTesterSimulator,
    "audio_freq_response": AudioFreqResponseSimulator,
    "delay_instability": DelayInstabilitySimulator,
    "signal_flow_scope": SignalFlowScopeSimulator,
    "nyquist_bode_comparison": NyquistBodeComparisonSimulator,
    "root_locus": RootLocusSimulator,
    "routh_hurwitz": RouthHurwitzSimulator,
    "nyquist_stability": NyquistStabilitySimulator,
    "controller_tuning_lab": ControllerTuningLabSimulator,
    "lead_lag_designer": LeadLagDesignerSimulator,
    "steady_state_error": SteadyStateErrorSimulator,
    "phase_portrait": PhasePortraitSimulator,
    "nonlinear_control_lab": NonlinearControlLabSimulator,
    "mimo_design_studio": MIMODesignStudioSimulator,
    "inverted_pendulum_3d": InvertedPendulum3DSimulator,
    "ball_beam_3d": BallBeam3DSimulator,
    "coupled_tanks_3d": CoupledTanks3DSimulator,
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
    "DifferenceEquationSimulator",
    "FeedbackAmplifierSimulator",
    "AmplifierSimulator",
    "LensOpticsSimulator",
    "FurutaPendulumSimulator",
    "BlockDiagramSimulator",
    "CyclicPathDetectorSimulator",
    "FeedbackConvergenceSimulator",
    "FundamentalModesSimulator",
    "SignalOperationsSimulator",
    "StateSpaceAnalyzerSimulator",
    "SamplingReconstructionSimulator",
    "MassSpringSimulator",
    "PolynomialMultiplicationSimulator",
    "OperatorAlgebraSimulator",
    "PoleBehaviorSimulator",
    "CascadeParallelSimulator",
    "DTCTComparatorSimulator",
    "ImpulseConstructionSimulator",
    "CTImpulseResponseSimulator",
    "ComplexPolesModesSimulator",
    "ZTransformPropertiesSimulator",
    "ZTransformROCSimulator",
    "InverseZTransformSimulator",
    "SystemRepresentationSimulator",
    "LaplaceROCSimulator",
    "LaplacePropertiesSimulator",
    "IVTFVTSimulator",
    "ODELaplaceSolverSimulator",
    "ResonanceAnatomySimulator",
    "EigenfunctionTesterSimulator",
    "VectorFreqResponseSimulator",
    "AudioFreqResponseSimulator",
    "DelayInstabilitySimulator",
    "SignalFlowScopeSimulator",
    "NyquistBodeComparisonSimulator",
    "RootLocusSimulator",
    "RouthHurwitzSimulator",
    "NyquistStabilitySimulator",
    "ControllerTuningLabSimulator",
    "LeadLagDesignerSimulator",
    "SteadyStateErrorSimulator",
    "PhasePortraitSimulator",
    "NonlinearControlLabSimulator",
    "MIMODesignStudioSimulator",
    "InvertedPendulum3DSimulator",
    "BallBeam3DSimulator",
    "CoupledTanks3DSimulator",
    "SIMULATOR_REGISTRY",
    "get_simulator_class",
    "is_simulator_available",
    "get_registered_simulators",
    "register_simulator",
]
