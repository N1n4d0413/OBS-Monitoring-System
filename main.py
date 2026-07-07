"""Console entry point for OBS Lecture Guard."""

from __future__ import annotations

import sys

from src.config.manager import ConfigManager
from src.obs.client import OBSClient
from src.obs.monitor import OBSMonitor
from src.utils.control import ControlManager, run_control_console
from src.vision.detector import PoseDetector


def main() -> None:
    """Load configuration and start the monitoring services."""
    control: ControlManager | None = None
    detector: PoseDetector | None = None

    try:
        if "--control-console" in sys.argv:
            run_control_console(sys.argv[-1])
            return

        config = ConfigManager().load()
        control = ControlManager()
        control.reset()
        control.start_console()

        detector = PoseDetector(config, debug=False)
        detector.start()

        obs = OBSClient(config)
        monitor = OBSMonitor(obs, detector, control)
        monitor.run()
    except KeyboardInterrupt:
        print("\nShutting down safely...")
    finally:
        if detector is not None:
            detector.stop()
        if control is not None:
            control.close_console()


if __name__ == "__main__":
    main()
