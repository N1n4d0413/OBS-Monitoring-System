"""Runtime debug control console for the monitoring app."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.utils.logger import log


@dataclass(frozen=True)
class ControlCommand:
    """Current runtime control state."""

    debug: bool = True
    exit_requested: bool = False


class ControlManager:
    """Share debug and exit commands between the app and control console."""

    def __init__(self, path: str | Path = "app_control.json") -> None:
        self.path = Path(path).resolve()
        self._last_debug: bool | None = None

    def reset(self) -> None:
        """Reset runtime control state before the monitor starts."""
        self.write(debug=True, exit_requested=False)

    def get_debug_mode(self) -> bool:
        """Return current debug setting."""
        return self.read().debug

    def read(self) -> ControlCommand:
        """Read the latest command from the runtime control file."""
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data: dict[str, Any] = json.load(file)
        except (OSError, json.JSONDecodeError):
            return ControlCommand()

        return ControlCommand(
            debug=bool(data.get("debug", True)),
            exit_requested=bool(data.get("exit_requested", False)),
        )

    def write(self, debug: bool, exit_requested: bool) -> None:
        """Write control state for the main monitor process."""
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "debug": debug,
                    "exit_requested": exit_requested,
                },
                file,
            )

    def start_console(self) -> None:
        """Open a separate terminal window for runtime debug commands."""
        args = self._console_args()
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

        try:
            subprocess.Popen(
                args,
                creationflags=creationflags,
                cwd=Path(__file__).resolve().parents[2],
            )
            log("Debug control console opened.")
        except OSError as error:
            log(f"Could not open debug control console: {error}")

    def _console_args(self) -> list[str]:
        if getattr(sys, "frozen", False):
            return [sys.executable, "--control-console", str(self.path)]

        project_main = Path(__file__).resolve().parents[2] / "main.py"
        return [sys.executable, str(project_main), "--control-console", str(self.path)]


def run_control_console(control_path: str) -> None:
    """Ask for debug commands until the user exits the whole app."""
    manager = ControlManager(control_path)
    command = manager.read()
    debug = command.debug

    while True:
        os.system("cls")
        state = "ON" if debug else "OFF"
        print("OBS Lecture Guard Debug Control")
        print(f"Debug mode is currently {state}")
        print()
        print("1 - Debug ON")
        print("2 - Debug OFF")
        print("3 - Exit whole app")
        choice = input("Choose option: ").strip().lower()

        if choice in {"1", "on"}:
            debug = True
            manager.write(debug=True, exit_requested=False)
            input("Debug mode ON. Press Enter to continue...")
        elif choice in {"2", "off"}:
            debug = False
            manager.write(debug=False, exit_requested=False)
            input("Debug mode OFF. Press Enter to continue...")
        elif choice in {"3", "exit", "q", "quit"}:
            manager.write(debug=debug, exit_requested=True)
            print("Exit requested. You can close this window.")
            return
        else:
            input("Invalid option. Press Enter to try again...")
