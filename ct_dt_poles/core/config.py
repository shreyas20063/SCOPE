class Config:
    """Configuration constants and styling"""

    # Professional color scheme
    COLORS = {
        'continuous': '#2980b9',
        'stable_discrete': '#27ae60',
        'unstable_discrete': '#e74c3c',
        'background': '#ecf0f1',
        'grid': '#bdc3c7',
        'accent': '#f39c12',
        'text': '#2c3e50'
    }

    # Figure layout parameters
    FIGURE_SIZE = (18, 12)
    FIGURE_FACECOLOR = '#f8f9fa'

    # Educational content
    METHOD_EXPLANATIONS = {
        'Forward Euler': {
            'formula': 'z = 1 + sT',
            'concept': 'Estimates derivatives by looking forward in time',
            'strength': 'Simple and intuitive implementation',
            'weakness': 'Can become unstable for large step sizes',
            'stability_limit': 'Stable only when T/τ < 2',
            'real_world': 'Used in real-time systems where simplicity matters'
        },
        'Backward Euler': {
            'formula': 'z = 1/(1-sT)',
            'concept': 'Estimates derivatives by looking backward in time',
            'strength': 'Inherently stable for all step sizes',
            'weakness': 'Can be overly conservative (too damped)',
            'stability_limit': 'Always stable if CT system is stable',
            'real_world': 'Preferred for stiff differential equations'
        },
        'Trapezoidal': {
            'formula': 'z = (1+sT/2)/(1-sT/2)',
            'concept': 'Averages forward and backward estimates',
            'strength': 'Best accuracy and stability balance',
            'weakness': 'Slightly more complex to implement',
            'stability_limit': 'Maps imaginary axis to unit circle exactly',
            'real_world': 'Industry standard for most applications'
        }
    }

    GUIDED_SCENARIOS = [
        {'T_tau': 0.3, 'method': 'Forward Euler', 'message': 'Start here: Small step size, very stable'},
        {'T_tau': 1.0, 'method': 'Forward Euler', 'message': 'Moderate step size, still stable but see the difference'},
        {'T_tau': 1.8, 'method': 'Forward Euler', 'message': 'Getting close to instability limit'},
        {'T_tau': 2.2, 'method': 'Forward Euler', 'message': 'UNSTABLE! See the oscillations'},
        {'T_tau': 2.2, 'method': 'Backward Euler', 'message': 'Same step size, but now stable with Backward Euler'},
        {'T_tau': 2.2, 'method': 'Trapezoidal', 'message': 'Trapezoidal also handles large steps well'}
    ]
