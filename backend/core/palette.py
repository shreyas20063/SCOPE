"""Standard plot color palette per CLAUDE.md design system.

Single source of truth for plot trace colors. Import these constants
instead of defining color hex strings as class constants in simulators.
"""

# Primary trace colors
BLUE = "#3b82f6"       # input signal, primary trace
RED = "#ef4444"        # output signal, secondary trace
GREEN = "#10b981"      # reference lines, cutoff markers
TEAL = "#14b8a6"       # accent traces
AMBER = "#f59e0b"      # warning, highlighting
PURPLE = "#7c3aed"     # accent
CYAN = "#06b6d4"       # signal processing category
PINK = "#ec4899"       # optics category

# Extended colors used in specific simulators
VIOLET = "#a855f7"     # jω-axis, secondary accent

# Plot chrome
PAPER_BG = "#0a0e27"
PLOT_BG = "#131b2e"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "rgba(148, 163, 184, 0.15)"
ZEROLINE_COLOR = "rgba(148, 163, 184, 0.3)"
LEGEND_BG = "rgba(15, 23, 42, 0.8)"
LEGEND_BORDER = "rgba(148, 163, 184, 0.2)"

# Stability fills
STABLE_FILL = "rgba(16, 185, 129, 0.05)"    # subtle green LHP
UNSTABLE_FILL = "rgba(239, 68, 68, 0.05)"   # subtle red RHP
