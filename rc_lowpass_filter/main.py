"""Entry point for the RC Lowpass Filter simulator."""

from rc_lowpass import RCFilterSimulator
from rc_lowpass.config import project_banner


def main() -> None:
    print(project_banner())
    simulator = RCFilterSimulator()
    simulator.run()


if __name__ == "__main__":
    main()
