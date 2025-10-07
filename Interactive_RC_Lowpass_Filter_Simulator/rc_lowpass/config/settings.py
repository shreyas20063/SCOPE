"""
Shared configuration constants and metadata for the RC Lowpass Filter
Simulator project.

This simulator is developed for the Signals and Systems course
(course code: EE204T) under Prof. Ameer Mulla by
Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

# Default circuit parameters
DEFAULT_RC_SECONDS = 0.001  # 1 ms time constant
DEFAULT_FREQUENCY_HZ = 100.0
DEFAULT_AMPLITUDE_V = 5.0

# Slider ranges
FREQUENCY_RANGE_HZ = (1, 300)
RC_RANGE_MS = (0.1, 10.0)  # sliders operate in milliseconds
AMPLITUDE_RANGE_V = (1.0, 10.0)

# Simulation resolution
TIME_WINDOW_SECONDS = 0.05
TIME_SAMPLES = 1000

# Frequency-domain settings
BODE_FREQUENCY_DECADE_RANGE = (-1, 5)  # log10 span
MAX_HARMONIC_ORDER = 39  # odd harmonics up to 39th (inclusive)
MAGNITUDE_FLOOR_DB = -80.0

# Status classification thresholds for f/fc ratio
STATUS_THRESHOLDS = {
    "passing": 0.3,
    "transitioning": 1.5,
}

# Presentation strings
COURSE_INFO = (
    "Signals and Systems (EE204T) project under Prof. Ameer Mulla "
    "by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar."
)

def project_banner() -> str:
    """Return the console banner shown at startup."""
    header = "=" * 70
    highlights = [
        "✓ Starts in PAUSED state (ready to play)",
        "✓ Smooth continuous animation (waveform slides)",
        "✓ Sliders work in BOTH paused and running states",
        "✓ Fixed constant time axis (50ms oscilloscope-style)",
        "✓ Fixed numerical stability (RC minimum is 0.1ms)",
        "✓ Reset button pauses the simulation",
        "✓ No recursion or blocking issues",
        "✓ All sliders update labels properly",
        "✓ Play/Pause button works perfectly",
        "✓ Beautiful UI matching web interface",
        "✓ Fixed Y-axis scale",
        "✓ Frequency range: 1-300 Hz",
        "✓ RC range: 0.1-10.0 ms (numerically stable)",
    ]
    controls = [
        "  • Click '▶ Play' button to start animation",
        "  • Drag sliders to adjust parameters in real-time",
        "  • Sliders update graphs even when paused!",
        "  • '|| Pause' / '▶ Play' button to control animation",
        "  • '↻ Reset' button returns to defaults AND pauses",
    ]

    return (
        f"{header}\n"
        "RC LOWPASS FILTER SIMULATOR - FINAL COMPLETE VERSION\n"
        f"{header}\n\n"
        f"{COURSE_INFO}\n\n"
        "Highlights:\n"
        + "\n".join(highlights)
        + "\n\nControls:\n"
        + "\n".join(controls)
        + "\n\n"
        + header
        + "\nStarting simulation...\n"
    )
