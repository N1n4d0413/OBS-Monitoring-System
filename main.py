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
    try:
        if "--control-console" in sys.argv:
            run_control_console(sys.argv[-1])
            return

        config = ConfigManager().load()
        control = ControlManager()
        control.reset()
        control.start_console()

        obs = OBSClient(config)
        detector = PoseDetector(config, debug=control.get_debug_mode())
        detector.start()

        monitor = OBSMonitor(obs, detector, control)
        monitor.run()
    except KeyboardInterrupt:
        print("\nShutting down safely...")


if __name__ == "__main__":
    main()
