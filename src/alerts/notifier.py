"""Console application sound notifications."""

from __future__ import annotations

import time
import winsound


class AlertManager:
    """Play the same Windows beep patterns used by the legacy tool."""

    def beep_mute(self) -> None:
        """Play the long mute warning beep."""
        winsound.Beep(1400, 3000)

    def beep_silence(self) -> None:
        """Play the double beep silence warning."""
        winsound.Beep(1000, 500)
        time.sleep(0.1)
        winsound.Beep(1000, 500)
