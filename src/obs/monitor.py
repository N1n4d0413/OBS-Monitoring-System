"""Main OBS monitoring loop coordination."""

from __future__ import annotations

import time

from src.audio.monitor import AudioMonitor
from src.obs.client import OBSClient
from src.utils.control import ControlManager
from src.utils.logger import log
from src.vision.detector import PoseDetector


class OBSMonitor:
    """Coordinate recording, OBS camera source, video state, and audio alerts."""

    CHECK_INTERVAL = 2

    def __init__(
        self,
        obs_client: OBSClient,
        detector: PoseDetector,
        control: ControlManager | None = None,
    ) -> None:
        self.obs = obs_client
        self.detector = detector
        self.config = detector.config
        self.audio = AudioMonitor(obs_client, self.config)
        self.control = control
        self.previous_recording_state = False
        self.previous_camera_source_state: bool | None = None
        self.previous_virtual_camera_state: bool | None = None

    def run(self) -> None:
        """Run the console monitor until interrupted."""
        log(f"OBS Monitor Started (Video Enabled: {self.detector.enabled})")

        try:
            while True:
                if self._apply_control_commands():
                    break

                camera_source_enabled = self.obs.is_camera_enabled(self.config["camera_source"])
                virtual_camera_active = self.obs.is_virtual_camera_active()
                self._log_camera_state(camera_source_enabled, virtual_camera_active)

                camera_active = camera_source_enabled and virtual_camera_active
                self.detector.set_camera_active(camera_active)

                record_status = self.obs.get_record_status()
                if record_status is None:
                    continue

                is_recording = bool(record_status.output_active)
                current_time = time.time()

                self._handle_recording_transition(is_recording, camera_active, current_time)

                if not is_recording:
                    self.previous_recording_state = is_recording
                    time.sleep(self.CHECK_INTERVAL)
                    continue

                self.audio.check(camera_active, self.detector.get_person_status(), current_time)
                self.previous_recording_state = is_recording
                time.sleep(self.CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("Shutting down safely...")
            self.detector.stop()
        except Exception as error:
            log(f"Unexpected error: {error}")
            self.detector.stop()
        finally:
            self.detector.stop()
            if self.control is not None:
                self.control.close_console()

    def _handle_recording_transition(
        self,
        is_recording: bool,
        camera_active: bool,
        current_time: float,
    ) -> None:
        if is_recording and not self.previous_recording_state:
            log("Recording started.")
            self.detector.reset_previous_person_state()
            self.audio.on_recording_started(
                camera_active,
                self.detector.get_person_status(),
                current_time,
            )

        if not is_recording and self.previous_recording_state:
            log("Recording stopped.")
            self.audio.on_recording_stopped()

    def _apply_control_commands(self) -> bool:
        if self.control is None:
            return False

        command = self.control.read()
        self.detector.set_debug(command.debug)

        if command.exit_requested:
            log("Exit requested from debug control console.")
            return True

        return False

    def _log_camera_state(self, camera_source_enabled: bool, virtual_camera_active: bool) -> None:
        if camera_source_enabled != self.previous_camera_source_state:
            state = "enabled" if camera_source_enabled else "disabled"
            log(f"OBS camera source is {state}.")
            self.previous_camera_source_state = camera_source_enabled

        if virtual_camera_active != self.previous_virtual_camera_state:
            state = "active" if virtual_camera_active else "inactive"
            log(f"OBS Virtual Camera is {state}.")
            self.previous_virtual_camera_state = virtual_camera_active
