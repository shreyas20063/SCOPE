"""Entry point for the Fourier series visualizer.

Prepared for the Signals and Systems course (EE204T) under
Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from gui.visualizer import FourierSeriesVisualizer


def main() -> None:
    """Launch the interactive visualizer."""
    visualizer = FourierSeriesVisualizer()
    visualizer.show()


if __name__ == "__main__":
    main()
