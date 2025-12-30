"""
System Calculator Module
Handles transfer function calculations and pole-zero analysis
"""

import numpy as np
from scipy import signal


class SystemCalculator:
    """Calculates system transfer functions and analyzes poles/zeros"""

    @staticmethod
    def get_system(model_type, alpha, beta, gamma, p):
        """
        Calculate system transfer function based on model type

        Parameters:
        -----------
        model_type : str
            'First-Order' or 'Second-Order'
        alpha : float
            Amplifier gain
        beta : float
            Feedback gain
        gamma : float
            Motor constant
        p : float
            Lag pole location

        Returns:
        --------
        tuple : (TransferFunction, poles, zeros)
        """
        if model_type == 'First-Order':
            return SystemCalculator._first_order_system(alpha, beta, gamma)
        else:
            return SystemCalculator._second_order_system(alpha, beta, gamma, p)

    @staticmethod
    def _first_order_system(alpha, beta, gamma):
        """
        Calculate first-order closed-loop system
        Transfer function: αγ/(s + αβγ)
        """
        num = [alpha * gamma]
        den = [1, alpha * beta * gamma]
        poles = np.array([-alpha * beta * gamma])
        zeros = np.array([])

        return signal.TransferFunction(num, den), poles, zeros

    @staticmethod
    def _second_order_system(alpha, beta, gamma, p):
        """
        Calculate second-order closed-loop system
        Transfer function: αγp/(s² + ps + αβγp)
        """
        num = [alpha * gamma * p]
        den = [1, p, alpha * beta * gamma * p]

        # Calculate poles: s = -p/2 ± sqrt((p/2)² - αβγp)
        discriminant = (p/2)**2 - alpha * beta * gamma * p

        if discriminant >= 0:
            # Real poles (overdamped)
            poles = np.array([
                -p/2 + np.sqrt(discriminant),
                -p/2 - np.sqrt(discriminant)
            ])
        else:
            # Complex conjugate poles (underdamped)
            real_part = -p/2
            imag_part = np.sqrt(-discriminant)
            poles = np.array([
                complex(real_part, imag_part),
                complex(real_part, -imag_part)
            ])

        zeros = np.array([])

        return signal.TransferFunction(num, den), poles, zeros
