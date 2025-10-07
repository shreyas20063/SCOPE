"""
Visualization module for the Feedback Amplifier Simulator
Contains all plotting and UI rendering functions
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.image as mpimg

from config import (COLORS, PANEL_COLORS, STEP_RESPONSE_Y_MAX, 
                    S_PLANE_X_MIN, S_PLANE_X_MAX)
from calculations import format_value

def plot_step_response(ax, t, ol_response, cl_response, metrics):
    """Plot step response comparison"""
    ax.clear()
    
    ax.plot(t, ol_response, color=COLORS['open_loop'], lw=2.5, 
            label='Open-Loop', linestyle='--', alpha=0.8)
    ax.plot(t, cl_response, color=COLORS['closed_loop'], lw=2.5, 
            label='Closed-Loop')
    
    ax.set_title('Step Response', fontsize=14, fontweight='bold', 
                 color=COLORS['title'])
    ax.set_xlabel('Time (s)', fontweight='bold')
    ax.set_ylabel('Output Voltage (V)', fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, STEP_RESPONSE_Y_MAX)
    ax.set_xlim(0, t[-1])
    
    text = f"Speedup: {metrics['speedup']:.1f}x\nCL Rise Time: {format_value(metrics['cl_rise_time'], 's')}"
    ax.text(0.98, 0.05, text, transform=ax.transAxes, ha='right', va='bottom',
            fontsize=9, fontweight='bold', 
            bbox=dict(boxstyle='round,pad=0.5', fc='#ffffff', ec=COLORS['edge'], alpha=0.9))

def plot_bode_magnitude(ax, omega, mag_ol, mag_cl, metrics):
    """Plot Bode magnitude comparison"""
    ax.clear()
    
    ax.semilogx(omega, mag_ol, color=COLORS['open_loop'], lw=2.5, 
                label='Open-Loop', linestyle='--', alpha=0.8)
    ax.semilogx(omega, mag_cl, color=COLORS['closed_loop'], lw=2.5, 
                label='Closed-Loop')
    
    ax.set_title('Bode Magnitude Plot', fontsize=14, fontweight='bold', 
                 color=COLORS['title'])
    ax.set_xlabel('Frequency (rad/s)', fontweight='bold')
    ax.set_ylabel('Magnitude (dB)', fontweight='bold')
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, alpha=0.3, which='both')
    
    y_min = min(mag_ol.min(), mag_cl.min())
    y_max = max(mag_ol.max(), mag_cl.max())
    y_range = y_max - y_min
    ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
    ax.set_xlim(omega[0], omega[-1])
    
    text = f"BW Extension: {metrics['speedup']:.1f}x\nCL Bandwidth: {format_value(metrics['cl_bw'], 'rad/s')}"
    ax.text(0.98, 0.05, text, transform=ax.transAxes, ha='right', va='bottom',
            fontsize=9, fontweight='bold', 
            bbox=dict(boxstyle='round,pad=0.5', fc='#ffffff', ec=COLORS['edge'], alpha=0.9))

def plot_bode_phase(ax, omega, phase_ol, phase_cl):
    """Plot Bode phase comparison"""
    ax.clear()
    
    ax.semilogx(omega, phase_ol, color=COLORS['open_loop'], lw=2.5, 
                label='Open-Loop', linestyle='--', alpha=0.8)
    ax.semilogx(omega, phase_cl, color=COLORS['closed_loop'], lw=2.5, 
                label='Closed-Loop')
    
    ax.set_title('Bode Phase Plot', fontsize=14, fontweight='bold', 
                 color=COLORS['title'])
    ax.set_xlabel('Frequency (rad/s)', fontweight='bold')
    ax.set_ylabel('Phase (degrees)', fontweight='bold')
    ax.set_yticks([-90, -45, 0])
    ax.set_ylim(-95, 5)
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim(omega[0], omega[-1])

def plot_s_plane(ax, metrics):
    """Plot s-plane with pole locations"""
    ax.clear()
    ol_pole, cl_pole = metrics['ol_pole'], metrics['cl_pole']
    
    ax.set_title('Pole Location (s-plane)', fontsize=14, fontweight='bold', 
                 color=COLORS['title'])
    ax.plot(ol_pole, 0, 'x', markersize=12, markeredgewidth=3, 
            color=COLORS['open_loop'], label='Open-Loop Pole')
    ax.plot(cl_pole, 0, 'o', markersize=10, markerfacecolor='none', 
            markeredgewidth=2.5, color=COLORS['closed_loop'], label='Closed-Loop Pole')
    
    if not np.isclose(ol_pole, cl_pole, rtol=0.01):
        ax.add_patch(FancyArrowPatch((ol_pole, 0.15), (cl_pole, 0.15), 
                                     arrowstyle='->', mutation_scale=20, lw=2, color='#333333'))
    
    ax.axhline(0, color='#888888', lw=1)
    ax.axvline(0, color='#888888', lw=1)
    ax.set_xlim(S_PLANE_X_MIN, S_PLANE_X_MAX)
    ax.set_ylim(-1, 1)
    ax.get_yaxis().set_ticks([])
    ax.set_xlabel('σ (Real Axis)', fontweight='bold')
    ax.set_ylabel('jω', fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)

def plot_info_panel(ax, K0, alpha, beta, input_amp):
    """Display system equations and parameters"""
    ax.clear()
    ax.axis('off')
    
    bg_color, edge_color = PANEL_COLORS['info']
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", 
                                transform=ax.transAxes, 
                                facecolor=bg_color, edgecolor=edge_color, linewidth=2))
    
    ax.text(0.5, 0.88, 'System Equations', ha='center', fontsize=13, 
            fontweight='bold', color=COLORS['title'])
    
    eq_ol = r'Open-Loop: $K(s) = \frac{\alpha K_0}{s + \alpha}$'
    eq_cl = r'Closed-Loop: $H(s) = \frac{\alpha K_0}{s + \alpha(1+\beta K_0)}$'
    ax.text(0.5, 0.58, f"{eq_ol}\n\n{eq_cl}", ha='center', va='center', 
            fontsize=10, linespacing=1.8)
    
    param_text = f"Current Parameters:\nβ={beta:.4f} | K₀={format_value(K0)}\nα={alpha:.1f} rad/s | Input={input_amp:.2f} V"
    ax.text(0.5, 0.18, param_text, ha='center', va='center', 
            fontsize=8.5, fontweight='bold', linespacing=1.6)

def plot_metrics_panel(ax, metrics):
    """Display performance metrics"""
    ax.clear()
    ax.axis('off')
    
    bg_color, edge_color = PANEL_COLORS['metrics']
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", 
                                transform=ax.transAxes, 
                                facecolor=bg_color, edgecolor=edge_color, linewidth=2))
    
    ax.text(0.5, 0.94, 'Performance Metrics', ha='center', fontsize=11, 
            fontweight='bold', color=COLORS['success'])
    
    # Open-Loop metrics
    ax.text(0.08, 0.82, 'Open-Loop', va='top', fontweight='bold', 
            color=COLORS['open_loop'], fontsize=9.5)
    ax.text(0.08, 0.73, f"Gain:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.73, f"{format_value(metrics['ol_gain'])}", va='top', fontsize=8)
    ax.text(0.08, 0.65, f"BW:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.65, f"{format_value(metrics['ol_bw'], 'rad/s')}", va='top', fontsize=8)
    ax.text(0.08, 0.57, f"Rise Time:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.57, f"{format_value(metrics['ol_rise_time'], 's')}", va='top', fontsize=8)
    ax.text(0.08, 0.49, f"Pole:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.49, f"{metrics['ol_pole']:.1f}", va='top', fontsize=8)
    
    # Closed-Loop metrics
    ax.text(0.08, 0.38, 'Closed-Loop', va='top', fontweight='bold', 
            color=COLORS['closed_loop'], fontsize=9.5)
    ax.text(0.08, 0.29, f"Gain:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.29, f"{format_value(metrics['cl_gain'])}", va='top', fontsize=8)
    ax.text(0.08, 0.21, f"BW:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.21, f"{format_value(metrics['cl_bw'], 'rad/s')}", va='top', fontsize=8)
    ax.text(0.08, 0.13, f"Rise Time:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.13, f"{format_value(metrics['cl_rise_time'], 's')}", va='top', fontsize=8)
    ax.text(0.08, 0.05, f"Pole:", va='top', fontsize=8, fontweight='bold')
    ax.text(0.35, 0.05, f"{metrics['cl_pole']:.1f}", va='top', fontsize=8)

def plot_block_diagram(ax):
    """Display feedback system block diagram"""
    ax.clear()
    ax.axis('off')
    
    image_path = ''
    try:
        script_dir = os.path.dirname(__file__)
        image_filename = 'image_1dc166.png'
        image_path = os.path.join(script_dir, image_filename)
        
        img = mpimg.imread(image_path)
        ax.imshow(img)
    except Exception:
        error_text = f'Error: Image not found.\nAttempted path:\n{image_path}'
        ax.text(0.5, 0.5, error_text, ha='center', va='center', fontsize=8, 
                color='red', wrap=True,
                bbox=dict(boxstyle='round,pad=0.5', fc='#ffebee', ec='#c62828'))
