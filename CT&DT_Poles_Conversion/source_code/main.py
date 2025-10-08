from problemGenerator import ProblemGenerator
from problemGenerator import AssessmentTools
from visualisation import PlotRenderer, UserInterface
from mathHandler import SystemMath
from config import Config
from eduContent import EducationalContent

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation



class TeachingUtils:
    """Utilities for instructors and teaching"""
    
    @staticmethod
    def create_lecture_slides():
        """Generate key teaching points for lectures"""
        teaching_points = {
            'Introduction': [
                "Why do we need discrete-time approximations?",
                "Real systems are implemented digitally",
                "Computers can't handle continuous derivatives directly"
            ],
            'Forward Euler Intuition': [
                "Look ahead to estimate the slope",
                "Simple but can overshoot", 
                "Like driving while only looking far ahead"
            ],
            'Backward Euler Intuition': [
                "Look behind to understand what happened",
                "Conservative and stable",
                "Like driving while looking in rearview mirror"
            ],
            'Trapezoidal Intuition': [
                "Balance between forward and backward",
                "Best of both worlds",
                "Like looking both ahead and behind"
            ],
            'Key Insights': [
                "Unit circle in z-plane = stability boundary",
                "Forward Euler: watch out for T/τ > 2",
                "Backward Euler: always stable if CT is stable",
                "Trapezoidal: maps jω axis to unit circle exactly"
            ]
        }
        
        return teaching_points
    
    @staticmethod
    def run_instructor_mode():
        """Special mode for instructors with advanced controls"""
        print("\nINSTRUCTOR MODE: Advanced Teaching Controls")
        print("-"*45)
        
        # Allow custom scenarios
        tau_custom = float(input("Enter time constant τ (default 1.0): ") or 1.0)
        
        explorer = CT_DT_Educational_Explorer()
        explorer.tau = tau_custom
        
        # Pre-load interesting scenarios
        scenarios = [
            {'name': 'Stable Forward Euler', 'T_tau': 0.8, 'method': 'Forward Euler'},
            {'name': 'Unstable Forward Euler', 'T_tau': 2.5, 'method': 'Forward Euler'},
            {'name': 'Robust Backward Euler', 'T_tau': 2.5, 'method': 'Backward Euler'},
            {'name': 'Accurate Trapezoidal', 'T_tau': 1.5, 'method': 'Trapezoidal'}
        ]
        
        print("\nPre-loaded scenarios for demonstration:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario['name']} (T/τ = {scenario['T_tau']}, {scenario['method']})")
        
        return explorer, scenarios


# =============================================================================
# MAIN EXPLORER CLASS
# =============================================================================

class CT_DT_Educational_Explorer:
    """Main class for the educational tool"""
    
    def __init__(self):
        # Initialize system parameters
        self.tau = 1.0
        self.T = 0.5
        self.method = 'Forward Euler'
        self.learning_mode = 'explore'
        self.current_scenario = 0
        self.animation_running = False
        
        # Setup figure and styling
        self._setup_figure_and_style()
        
        # Create subplot layout
        self._create_subplot_layout()
        
        # Initialize components
        self.renderer = PlotRenderer(self.fig, self.axes, Config.COLORS)
        self.ui = UserInterface(self.fig, self)
        
        # Initial update
        self.update_all_visualizations()
    
    def _setup_figure_and_style(self):
        """Setup figure styling and properties"""
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        self.fig = plt.figure(figsize=Config.FIGURE_SIZE)

        self.fig.patch.set_facecolor(Config.FIGURE_FACECOLOR)
        
        
        self.fig.set_size_inches(18, 14)  # Make figure bigger
        plt.tight_layout(pad=20.0)         # Add generous padding
        plt.subplots_adjust(bottom=0.15, top=0.93, wspace=0.6, hspace=0.8)

                # Global subplot breathing room
        self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.1, 
                                wspace=0.35, hspace=0.4)
        self.fig.tight_layout(pad=2.0, w_pad=1.5, h_pad=2.0)

        # Clear, educational title
        self.fig.suptitle('Continuous to Discrete-Time System Transformation', 
                         fontsize=14, fontweight='bold', color=Config.COLORS['text'], y=0.95)
    
    def _create_subplot_layout(self):
        """Create comprehensive subplot layout"""
        gs = self.fig.add_gridspec(3, 4, height_ratios=[1.2, 1.2, 0.4], width_ratios=[1, 1, 1, 1],
                                  hspace=0.9, wspace=0.9)
        
        self.axes = {
            's_plane': self.fig.add_subplot(gs[0, 0]),
            'z_plane': self.fig.add_subplot(gs[0, 1]),
            'step_response': self.fig.add_subplot(gs[0, 2:4]),
            'stability_map': self.fig.add_subplot(gs[1, 0]),
            'pole_trajectory': self.fig.add_subplot(gs[1, 1]),
            'learning_panel': self.fig.add_subplot(gs[1, 2:4])
        }
        # ADD SPACING FIX HERE (after subplots are created):
        self.fig.set_size_inches(18, 14)
        # self.fig.tight_layout(pad=30.0)
        self.fig.subplots_adjust(bottom=0.15, top=0.88, wspace=0.35, hspace=0.45)
    
    # =============================================================================
    # EVENT HANDLERS
    # =============================================================================
    
    def update_step_size(self, val):
        """Update when student changes T/τ ratio"""
        self.T = val * self.tau
        self.update_all_visualizations()
        EducationalContent.provide_real_time_feedback(self.T, self.tau, self.method)
        
    def change_method(self, method):
        """Update when student selects different method"""
        self.method = method
        self.update_all_visualizations()
        EducationalContent.explain_method_change(method)
    
    def start_guided_mode(self, event):
        """Begin step-by-step guided exploration"""
        self.learning_mode = 'guided'
        self.current_scenario = 0
        self.load_scenario(Config.GUIDED_SCENARIOS[0])
        print("\n=== GUIDED EXPLORATION MODE ===")
        print("Follow the scenarios to understand each method systematically...")
        
    def start_challenge_mode(self, event):
        # """Present challenges for advanced students"""
        # self.learning_mode = 'challenge'
        # challenges = [
        #     "Challenge 1: Find the exact T/τ where Forward Euler becomes unstable",
        #     "Challenge 2: Compare step response accuracy of all three methods at T/τ = 1.5", 
        #     "Challenge 3: Explain why Trapezoidal method maps jω axis to unit circle"
        # ]
        # print("\n=== CHALLENGE MODE ===")
        # for challenge in challenges:
        #     print(challenge)
        return
    
    def load_scenario(self, scenario):
        """Load a specific guided scenario"""
        self.ui.slider_T_tau.set_val(scenario['T_tau'])
        # Update method selection
        method_index = ['Forward Euler', 'Backward Euler', 'Trapezoidal'].index(scenario['method'])
        self.ui.radio_method.set_active(method_index)
        self.method = scenario['method']
        print(f"Scenario: {scenario['message']}")
    
    def run_demo_animation(self, event):
        """Run automatic demonstration"""
        print("\nRunning automated demonstration...")
        
        # Animation sequence: sweep T/τ from 0.1 to 3.0 and back
        T_tau_sequence = np.concatenate([
            np.linspace(3.0, 0.1, 80),   # Backward sweep
            np.linspace(0.1, 3.0, 80),   # Forward sweep
        ])
        
        def animate_frame(frame):
            if frame < len(T_tau_sequence) and not self.animation_running:
                return []
            self.ui.slider_T_tau.set_val(T_tau_sequence[frame % len(T_tau_sequence)])
            return []
            
        self.animation = animation.FuncAnimation(
            self.fig, animate_frame, frames=len(T_tau_sequence),
            interval=100, repeat=True, blit=False
        )
        self.animation_running = True
        
    def reset_to_defaults(self, event):
        """Reset simulation to initial state"""
        self.animation_running = False
        if hasattr(self, 'animation'):
            self.animation.event_source.stop()
            
        self.ui.slider_T_tau.reset()
        self.ui.radio_method.set_active(0)
        self.method = 'Forward Euler' 
        self.learning_mode = 'explore'
        self.update_all_visualizations()
        print("\nReset to default configuration")
    
    # =============================================================================
    # MAIN UPDATE METHODS
    # =============================================================================
    
    def update_all_visualizations(self):
        """Update all plots and displays"""
        self.renderer.plot_s_plane_enhanced(self.tau, self.T, self.method)
        self.renderer.plot_z_plane_enhanced(self.tau, self.T, self.method)
        self.renderer.plot_step_response_comparison(self.tau, self.T, self.method)
        self.renderer.plot_stability_landscape(self.tau, self.T, self.method)
        self.renderer.plot_pole_movement_visualization(self.tau, self.T, self.method)
        self.renderer.create_learning_panel(self.tau, self.T, self.method)
        
        # Status display
        s_pole = SystemMath.get_ct_pole(self.tau)
        z_pole = SystemMath.get_dt_pole(s_pole, self.T, self.method)
        
        status_info = f"""System Configuration: τ={self.tau:.2f}s  |  T={self.T:.2f}s  |  T/τ={self.T/self.tau:.2f}  |  Method: {self.method}  |  Status: {"STABLE" if abs(z_pole) < 1 else "UNSTABLE"}"""
        
        self.fig.text(0.5, 0.02, status_info, ha='center', fontsize=9, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.4", facecolor='white', alpha=0.95))
        
        plt.draw()


# =============================================================================
# MAIN EXECUTION FUNCTIONS
# =============================================================================

def run_classroom_demo():
    """Launch the educational demonstration for classroom use"""
    print("6.003 SIGNALS AND SYSTEMS: Interactive Pole Mapping Laboratory")
    print("=" * 70)
    print("PURPOSE: Understand how continuous-time system poles transform")
    print("         to discrete-time through numerical integration methods")
    print("\nLEARNING GOALS:")
    print("  1. Visualize s-plane to z-plane transformations")
    print("  2. Understand stability implications of step size choice")
    print("  3. Compare Forward Euler, Backward Euler, and Trapezoidal methods")
    print("  4. Connect theory to practical system behavior")
    print("\nINTERACTIVE FEATURES:")
    print("  • Real-time parameter adjustment")
    print("  • Visual stability feedback") 
    print("  • Step response comparisons")
    print("  • Guided exploration scenarios")
    print("  • Automatic demonstrations")
    print("\nCLASSROOM USAGE:")
    print("  • Instructor can guide students through scenarios")
    print("  • Students can explore at their own pace")
    print("  • Built-in assessment and feedback")
    print("  • Professional visualizations for presentations")
    print("=" * 70)
    
    explorer = CT_DT_Educational_Explorer()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15, left=0.12, top=0.88, right=0.98)
    plt.show()
    
    return explorer

def run_post_exploration_options():
    """Handle post-exploration learning resources"""
    print("\n" + "-"*50)
    print("ADDITIONAL LEARNING RESOURCES:")
    print("1. Take assessment quiz")
    print("2. Generate practice problems") 
    print("3. View teaching points summary")
    
    choice = input("\nSelect option (1-3) or press Enter to finish: ").strip()
    
    if choice == '1':
        AssessmentTools.run_assessment_quiz()
    elif choice == '2':
        ProblemGenerator.generate_problem_set()
    elif choice == '3':
        points = TeachingUtils.create_lecture_slides()
        print("\nKEY TEACHING POINTS:")
        for topic, bullets in points.items():
            print(f"\n{topic.upper()}:")
            for bullet in bullets:
                print(f"  • {bullet}")
    
    print("\n🎓 Session complete! Keep exploring to build deeper intuition.")



if __name__ == "__main__":
    # Check if instructor mode is requested
    mode = input("Choose mode - [S]tudent or [I]nstructor (default: Student): ").lower().strip()
    
    if mode.startswith('i'):
        explorer, scenarios = TeachingUtils.run_instructor_mode()
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15, left=0.12, top=0.88, right=0.98)
        plt.show()
    else:
        # Standard student mode
        explorer = run_classroom_demo()
    
    # Post-exploration options
    run_post_exploration_options()