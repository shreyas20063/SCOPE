import numpy as np
# =============================================================================
# MATHEMATICAL COMPUTATIONS
# =============================================================================

class SystemMath:
    """Mathematical computations for CT-DT transformations"""
    
    @staticmethod
    def get_ct_pole(tau):
        """Continuous-time pole for leaky tank: s = -1/τ"""
        return -1.0 / tau
    
    @staticmethod
    def get_dt_pole(s_pole, T, method):
        """Discrete-time pole using selected numerical method"""
        if method == 'Forward Euler':
            return 1 + s_pole * T
        elif method == 'Backward Euler':
            return 1 / (1 - s_pole * T)
        elif method == 'Trapezoidal':
            return (1 + s_pole * T/2) / (1 - s_pole * T/2)
    
    @staticmethod
    def analytical_step_response(t, tau):
        """Analytical continuous-time step response"""
        return (1 - np.exp(-t / tau)) * (t >= 0)
    
    @staticmethod
    def compute_discrete_step_response(n_samples, T, tau, method):
        """Compute discrete-time step response for current method"""
        y = np.zeros(n_samples, dtype=float)
        
        if method == 'Forward Euler':
            y_val = 0.0
            for i in range(n_samples):
                y_val = (1 - T/tau) * y_val + (T/tau)
                y[i] = y_val
                if abs(y_val) > 50:  # Prevent explosion
                    return y[:i+1]
                    
        elif method == 'Backward Euler':
            y_prev = 0.0
            for i in range(n_samples):
                y_val = (y_prev + T/tau) / (1 + T/tau)
                y[i] = y_val
                y_prev = y_val
                
        elif method == 'Trapezoidal':
            y_prev = 0.0
            x_prev = 0.0  # Previous input value
            for i in range(n_samples):
                t_current = i * T
                # Current input (step function)
                x_current = 1.0 if t_current >= 0 else 0.0
                
                # Correct trapezoidal rule implementation
                numerator = y_prev * (1 - T/(2*tau)) + (T/(2*tau)) * (x_current + x_prev)
                denominator = 1 + T/(2*tau)
                y_val = numerator / denominator
                
                y[i] = y_val
                y_prev = y_val
                x_prev = x_current
        return y
    
    @staticmethod
    def compute_stability_curve(T_tau_range, tau, method):
        """Compute pole magnitudes across T/τ range"""
        magnitudes = []
        s_pole = SystemMath.get_ct_pole(tau)
        
        for T_tau in T_tau_range:
            T_temp = T_tau * tau
            z_pole = SystemMath.get_dt_pole(s_pole, T_temp, method)
            magnitudes.append(abs(z_pole))
            
        return np.array(magnitudes)
    
    @staticmethod
    def compute_pole_trajectory(T_tau_values, tau, method):
        """Compute pole positions for trajectory visualization"""
        trajectory = []
        s_pole = SystemMath.get_ct_pole(tau)
        
        for T_tau in T_tau_values:
            T_temp = T_tau * tau
            z_pole = SystemMath.get_dt_pole(s_pole, T_temp, method)
            trajectory.append(z_pole)
            
        return trajectory
