"""
Core calculations module for the Feedback Amplifier Simulator
Contains all mathematical computations and signal processing functions
"""

import numpy as np

def calculate_metrics(K0, alpha, beta):
    """
    Calculate key performance metrics for both open-loop and closed-loop systems

    Parameters:
    -----------
    K0 : float
        Open-loop gain
    alpha : float
        Pole location (rad/s)
    beta : float
        Feedback factor

    Returns:
    --------
    dict : Dictionary containing all calculated metrics
    """
    loop_gain_factor = 1 + beta * K0
    closed_loop_gain = K0 / loop_gain_factor
    closed_loop_pole_loc = alpha * loop_gain_factor

    return {
        'ol_gain': K0,
        'cl_gain': closed_loop_gain,
        'ol_bw': alpha,
        'cl_bw': closed_loop_pole_loc,
        'ol_rise_time': 2.2 / alpha,
        'cl_rise_time': 2.2 / closed_loop_pole_loc,
        'ol_pole': -alpha,
        'cl_pole': -closed_loop_pole_loc,
        'speedup': loop_gain_factor,
    }

def calculate_step_response(K0, alpha, beta, input_amp, t):
    """
    Calculate step response for both open-loop and closed-loop systems

    Parameters:
    -----------
    K0 : float
        Open-loop gain
    alpha : float
        Pole location (rad/s)
    beta : float
        Feedback factor
    input_amp : float
        Input amplitude (V)
    t : numpy.ndarray
        Time array

    Returns:
    --------
    tuple : (open_loop_response, closed_loop_response)
    """
    metrics = calculate_metrics(K0, alpha, beta)

    ol_response = input_amp * K0 * (1 - np.exp(-alpha * t))
    cl_response = input_amp * metrics['cl_gain'] * (1 - np.exp(-metrics['cl_bw'] * t))

    return ol_response, cl_response

def calculate_bode_magnitude(K0, alpha, beta, omega):
    """
    Calculate Bode magnitude response for both systems

    Parameters:
    -----------
    K0 : float
        Open-loop gain
    alpha : float
        Pole location (rad/s)
    beta : float
        Feedback factor
    omega : numpy.ndarray
        Frequency array (rad/s)

    Returns:
    --------
    tuple : (ol_magnitude_db, cl_magnitude_db)
    """
    metrics = calculate_metrics(K0, alpha, beta)

    H_ol = (K0 * alpha) / (1j * omega + alpha)
    H_cl = (metrics['cl_gain'] * metrics['cl_bw']) / (1j * omega + metrics['cl_bw'])

    mag_ol = 20 * np.log10(np.abs(H_ol))
    mag_cl = 20 * np.log10(np.abs(H_cl))

    return mag_ol, mag_cl

def calculate_bode_phase(K0, alpha, beta, omega):
    """
    Calculate Bode phase response for both systems

    Parameters:
    -----------
    K0 : float
        Open-loop gain
    alpha : float
        Pole location (rad/s)
    beta : float
        Feedback factor
    omega : numpy.ndarray
        Frequency array (rad/s)

    Returns:
    --------
    tuple : (ol_phase_deg, cl_phase_deg)
    """
    metrics = calculate_metrics(K0, alpha, beta)

    phase_ol = np.angle((K0 * alpha) / (1j * omega + alpha), deg=True)
    phase_cl = np.angle((metrics['cl_gain'] * metrics['cl_bw']) / (1j * omega + metrics['cl_bw']), deg=True)

    return phase_ol, phase_cl

def format_value(value, unit=''):
    """
    Format numbers into human-readable strings with SI prefixes

    Parameters:
    -----------
    value : float
        Value to format
    unit : str
        Unit to append

    Returns:
    --------
    str : Formatted string
    """
    if value == 0:
        return f"0 {unit}"

    abs_val = abs(value)
    if abs_val >= 1e6:
        return f'{value/1e6:.2f}M{unit}'
    if abs_val >= 1e3:
        return f'{value/1e3:.2f}k{unit}'
    if abs_val >= 1:
        return f'{value:.2f}{unit}'
    if abs_val >= 1e-3:
        return f'{value*1e3:.2f}m{unit}'
    if abs_val >= 1e-6:
        return f'{value*1e6:.2f}µ{unit}'
    return f'{value*1e9:.2f}n{unit}'
