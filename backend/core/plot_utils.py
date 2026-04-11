"""Plotly layout helpers for consistent plot styling.

Centralizes the standard dark-theme layout pattern used across all simulators.
Color constants come from core.palette; this module handles structure.

Reference: CLAUDE.md "Plot Conventions" and "Design System" sections.
"""

from typing import Any, Dict, Optional


# Standard dark-theme values (from CLAUDE.md design system)
_PAPER_BG = "#0a0e27"
_PLOT_BG = "#131b2e"
_TEXT_COLOR = "#e2e8f0"
_FONT_FAMILY = "Inter, sans-serif"
_GRID_COLOR = "rgba(148, 163, 184, 0.1)"
_ZEROLINE_COLOR = "rgba(148, 163, 184, 0.3)"


def build_plotly_layout(
    title: str,
    xaxis_title: str = "",
    yaxis_title: str = "",
    *,
    uirevision: Optional[str] = None,
    showlegend: bool = True,
    margin: Optional[Dict[str, int]] = None,
    **overrides: Any,
) -> Dict[str, Any]:
    """Build a standard Plotly layout dict per project conventions.

    Args:
        title: Plot title text.
        xaxis_title: X-axis label.
        yaxis_title: Y-axis label.
        uirevision: Plotly uirevision string (preserves zoom/pan).
        showlegend: Whether to show the legend.
        margin: Custom margin dict. Defaults to {t:45, r:25, b:55, l:60}.
        **overrides: Additional layout keys merged at the top level.
            Use 'xaxis' and 'yaxis' dicts to override axis properties.

    Returns:
        Plotly layout dict ready for use in plot dicts.
    """
    layout: Dict[str, Any] = {
        "title": {
            "text": title,
            "font": {"size": 16, "color": _TEXT_COLOR},
        },
        "paper_bgcolor": _PAPER_BG,
        "plot_bgcolor": _PLOT_BG,
        "font": {
            "family": _FONT_FAMILY,
            "size": 12,
            "color": _TEXT_COLOR,
        },
        "xaxis": {
            "title": xaxis_title,
            "gridcolor": _GRID_COLOR,
            "zerolinecolor": _ZEROLINE_COLOR,
        },
        "yaxis": {
            "title": yaxis_title,
            "gridcolor": _GRID_COLOR,
            "zerolinecolor": _ZEROLINE_COLOR,
        },
        "margin": margin or {"t": 45, "r": 25, "b": 55, "l": 60},
        "showlegend": showlegend,
    }

    if uirevision is not None:
        layout["uirevision"] = uirevision

    # Merge overrides — for nested dicts like xaxis/yaxis, merge rather than replace
    for key, value in overrides.items():
        if key in ("xaxis", "yaxis") and isinstance(value, dict) and key in layout:
            layout[key].update(value)
        else:
            layout[key] = value

    return layout
