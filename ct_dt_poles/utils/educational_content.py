from core.config import Config
from core.math_handler import SystemMath


class EducationalContent:
    """Manages educational content, feedback, and learning modes"""

    @staticmethod
    def provide_real_time_feedback(T, tau, method):
        """Give immediate feedback as students explore"""
        s_pole = SystemMath.get_ct_pole(tau)
        z_pole = SystemMath.get_dt_pole(s_pole, T, method)
        T_tau = T / tau

        feedback_messages = []

        if method == 'Forward Euler':
            if T_tau > 2.0:
                feedback_messages.append("WARNING: Forward Euler is unstable! T/τ > 2")
            elif T_tau > 1.5:
                feedback_messages.append("CAUTION: Approaching Forward Euler stability limit")
            else:
                feedback_messages.append("Forward Euler: Stable operation")

        elif method == 'Backward Euler':
            feedback_messages.append("Backward Euler: Always stable for stable CT systems")

        elif method == 'Trapezoidal':
            feedback_messages.append("Trapezoidal: Excellent accuracy and stability")

        if abs(z_pole) > 1:
            feedback_messages.append(f"UNSTABLE: |z| = {abs(z_pole):.3f} > 1")
        else:
            feedback_messages.append(f"STABLE: |z| = {abs(z_pole):.3f} < 1")

        for msg in feedback_messages:
            print(f">> {msg}")

    @staticmethod
    def explain_method_change(method):
        """Explain what happens when method changes"""
        method_info = Config.METHOD_EXPLANATIONS[method]
        print(f"\n--- SWITCHED TO: {method} ---")
        print(f"Formula: {method_info['formula']}")
        print(f"Key insight: {method_info['concept']}")
        print(f"Best for: {method_info['real_world']}")

    @staticmethod
    def add_guided_mode_tips(learning_mode, current_scenario, ax_learning_panel):
        """Add learning tips for guided mode"""
        if learning_mode == 'guided' and current_scenario < len(Config.GUIDED_SCENARIOS):
            tip = f"GUIDED MODE - Step {current_scenario + 1}:\n{Config.GUIDED_SCENARIOS[current_scenario]['message']}"
            ax_learning_panel.text(0.05, 0.25, tip, transform=ax_learning_panel.transAxes,
                                 fontsize=9, verticalalignment='top',
                                 bbox=dict(boxstyle="round,pad=0.02", facecolor='lightyellow',
                                         alpha=0.7, edgecolor='orange', linewidth=1))
