"""Runtime path helpers for source and frozen executable runs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True when running as a PyInstaller executable."""
    return bool(getattr(sys, "frozen", False))


def runtime_dir() -> Path:
    """Return a writable directory for runtime files."""
    if not is_frozen():
        return Path.cwd()

    appdata = os.environ.get("APPDATA")
    if appdata:
        path = Path(appdata) / "OBS Lecture Guard"
    else:
        path = Path.home() / "OBS Lecture Guard"

    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_file(name: str) -> Path:
    """Return a writable runtime file path."""
    return runtime_dir() / name
