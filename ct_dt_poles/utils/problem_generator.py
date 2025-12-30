from core.math_handler import SystemMath


class AssessmentTools:
    """Tools for student assessment and evaluation"""

    @staticmethod
    def run_assessment_quiz():
        """Interactive assessment for student understanding"""
        print("\n" + "="*50)
        print("STUDENT ASSESSMENT: CT-to-DT Pole Mapping")
        print("="*50)

        questions = [
            {
                'question': 'For the leaky tank system, what happens to stability when T/τ exceeds 2 with Forward Euler?',
                'options': ['A) System becomes more accurate', 'B) System becomes unstable', 'C) No effect on stability', 'D) System becomes faster'],
                'correct': 'B',
                'explanation': 'Forward Euler becomes unstable when the discrete-time pole moves outside the unit circle, which happens when T/τ > 2 for the leaky tank system.'
            },
            {
                'question': 'Which numerical method preserves stability for ANY step size (assuming the CT system is stable)?',
                'options': ['A) Forward Euler', 'B) Backward Euler', 'C) Trapezoidal Rule', 'D) All methods are equivalent'],
                'correct': 'B',
                'explanation': 'Backward Euler maps the entire left half-plane of the s-domain inside the unit circle in the z-domain, ensuring stability preservation.'
            },
            {
                'question': 'What does the unit circle represent in the z-plane?',
                'options': ['A) Frequency response boundary', 'B) Accuracy threshold', 'C) Stability boundary', 'D) Computational limit'],
                'correct': 'C',
                'explanation': 'The unit circle is the stability boundary in the z-plane. Poles inside are stable, poles outside are unstable.'
            },
            {
                'question': 'The trapezoidal rule mapping formula is:',
                'options': ['A) z = 1 + sT', 'B) z = 1/(1-sT)', 'C) z = (1+sT/2)/(1-sT/2)', 'D) z = esT'],
                'correct': 'C',
                'explanation': 'The trapezoidal rule uses centered differences, resulting in the bilinear transformation z = (1+sT/2)/(1-sT/2).'
            }
        ]

        return AssessmentTools._process_quiz(questions)

    @staticmethod
    def _process_quiz(questions):
        """Process quiz questions and calculate score"""
        score = 0
        total = len(questions)

        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}: {question['question']}")
            for option in question['options']:
                print(f"    {option}")

            while True:
                answer = input("\nEnter your answer (A, B, C, or D): ").upper().strip()
                if answer in ['A', 'B', 'C', 'D']:
                    break
                print("Please enter A, B, C, or D")

            if answer == question['correct']:
                print(f"CORRECT! {question['explanation']}")
                score += 1
            else:
                print(f"INCORRECT. The correct answer is {question['correct']}.")
                print(f"Explanation: {question['explanation']}")

        AssessmentTools._display_final_score(score, total)
        return score / total

    @staticmethod
    def _display_final_score(score, total):
        """Display final assessment score with feedback"""
        print(f"\n" + "="*30)
        print(f"ASSESSMENT COMPLETE")
        print(f"Score: {score}/{total} ({100*score/total:.0f}%)")

        if score == total:
            print("OUTSTANDING! You've mastered the concepts!")
        elif score >= 0.75 * total:
            print("EXCELLENT! Strong understanding demonstrated!")
        elif score >= 0.5 * total:
            print("GOOD! You understand the basics, practice more for mastery!")
        else:
            print("NEEDS IMPROVEMENT: Review the concepts and try the simulation again!")


class ProblemGenerator:
    """Generate practice problems and homework scenarios"""

    @staticmethod
    def export_homework_scenarios():
        """Generate scenarios for homework problems"""
        scenarios = []
        methods = ['Forward Euler', 'Backward Euler', 'Trapezoidal']
        T_tau_values = [0.5, 1.0, 1.5, 2.0, 2.5]

        for method in methods:
            for T_tau in T_tau_values:
                # Calculate pole for this scenario
                tau = 1.0
                T = T_tau * tau
                s_pole = SystemMath.get_ct_pole(tau)
                z_pole = SystemMath.get_dt_pole(s_pole, T, method)

                scenarios.append({
                    'method': method,
                    'T_tau': T_tau,
                    'z_pole': z_pole,
                    'stable': abs(z_pole) < 1,
                    'magnitude': abs(z_pole)
                })

        return scenarios

    @staticmethod
    def generate_problem_set():
        """Generate practice problems for students"""
        print("\n" + "="*60)
        print("PRACTICE PROBLEM SET: CT-to-DT Pole Mapping")
        print("="*60)

        problems = [
            {
                'setup': 'A leaky tank system has τ = 0.5s. Using Forward Euler with T = 0.8s:',
                'questions': [
                    'a) Calculate T/τ ratio',
                    'b) Find the discrete-time pole location',
                    'c) Determine if the system is stable',
                    'd) Sketch the pole in both s and z planes'
                ],
                'solution': 'T/τ = 1.6, z = 1 + (-2)(0.8) = -0.6, |z| = 0.6 < 1 → STABLE'
            },
            {
                'setup': 'Compare Forward and Backward Euler for T/τ = 2.5:',
                'questions': [
                    'a) Calculate both discrete-time poles',
                    'b) Which method gives a stable system?',
                    'c) Explain the difference in behavior'
                ],
                'solution': 'FE: z = 1-2.5 = -1.5 (|z|=1.5 > 1, UNSTABLE), BE: z = 1/3.5 = 0.286 (STABLE)'
            }
        ]

        for i, problem in enumerate(problems, 1):
            print(f"\nPROBLEM {i}: {problem['setup']}")
            for question in problem['questions']:
                print(f"   {question}")
            print(f"\nSolution approach: {problem['solution']}")

        return problems
