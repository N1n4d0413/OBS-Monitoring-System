"""OBS microphone mute and silence monitoring."""

from __future__ import annotations

from typing import Any

from src.alerts.notifier import AlertManager
from src.obs.client import OBSClient
from src.utils.logger import log


class AudioMonitor:
    """Maintain microphone state and trigger duplicate-safe audio alerts."""

    ALERT_INTERVAL = 5
    SILENCE_THRESHOLD = -60
    SILENCE_DURATION = 15

    def __init__(
        self,
        obs_client: OBSClient,
        config: dict[str, Any],
        notifier: AlertManager | None = None,
        video_enabled: bool = True,
    ) -> None:
        self.obs = obs_client
        self.mic_name = config["mic_name"]
        self.notifier = notifier or AlertManager()
        self.video_enabled = video_enabled
        self.last_beep_time = 0.0
        self.silence_start_time: float | None = None
        self.previous_muted_state: bool | None = None
        self.audio_was_silent = False
        self.muted_alert_logged = False

    def on_recording_started(
        self,
        camera_active: bool,
        person_present: bool,
        current_time: float,
    ) -> None:
        """Reset audio state and warn if the mic is already muted."""
        mute_status = self.obs.get_input_mute(self.mic_name)
        if mute_status is None:
            return

        is_muted = bool(mute_status.input_muted)
        self.previous_muted_state = is_muted
        self.silence_start_time = None
        self.audio_was_silent = False
        self.muted_alert_logged = False

        if is_muted and self._should_alert_for_video(camera_active, person_present):
            log("Mic muted.")
            log("ALERT: Person detected, but mic is muted at recording start!")
            self.notifier.beep_mute()
            self.last_beep_time = current_time
            self.muted_alert_logged = True

    def on_recording_stopped(self) -> None:
        """Reset transient audio state after recording stops."""
        self.silence_start_time = None
        self.previous_muted_state = None
        self.audio_was_silent = False
        self.muted_alert_logged = False

    def check(self, camera_active: bool, person_present: bool, current_time: float) -> None:
        """Check mic mute and silence conditions for one monitor loop pass."""
        mute_status = self.obs.get_input_mute(self.mic_name)
        if mute_status is None:
            return

        is_muted = bool(mute_status.input_muted)
        if is_muted:
            self._handle_muted(camera_active, person_present, current_time)
        else:
            self._handle_unmuted(current_time)

        self.previous_muted_state = is_muted

    def _handle_muted(self, camera_active: bool, person_present: bool, current_time: float) -> None:
        self.silence_start_time = None
        self.audio_was_silent = False

        if self.previous_muted_state is not True:
            log("Mic muted.")
            self.muted_alert_logged = False

        if not self._should_alert_for_video(camera_active, person_present):
            return

        if self.previous_muted_state is False or not self.muted_alert_logged:
            log("ALERT: Person detected, but mic is muted.")
            self.notifier.beep_mute()
            self.last_beep_time = current_time
            self.muted_alert_logged = True
        elif current_time - self.last_beep_time >= self.ALERT_INTERVAL:
            log("ALERT: Person detected, but mic is still muted.")
            self.notifier.beep_mute()
            self.last_beep_time = current_time

    def _handle_unmuted(self, current_time: float) -> None:
        if self.previous_muted_state is True:
            log("Mic unmuted.")
            self.muted_alert_logged = False

        volume_info = self.obs.get_input_volume(self.mic_name)
        if volume_info is None:
            return

        volume_db = volume_info.input_volume_db
        if volume_db < self.SILENCE_THRESHOLD:
            self._handle_silence(current_time)
            return

        if self.audio_was_silent:
            log("Audio signal restored.")
        self.silence_start_time = None
        self.audio_was_silent = False

    def _handle_silence(self, current_time: float) -> None:
        if self.silence_start_time is None:
            self.silence_start_time = current_time
            return

        if current_time - self.silence_start_time < self.SILENCE_DURATION:
            return

        if not self.audio_was_silent:
            log("ALERT: No audio signal detected!")
            self.notifier.beep_silence()
            self.last_beep_time = current_time
            self.audio_was_silent = True
        elif current_time - self.last_beep_time >= self.ALERT_INTERVAL:
            self.notifier.beep_silence()
            self.last_beep_time = current_time

    def _should_alert_for_video(self, camera_active: bool, person_present: bool) -> bool:
        return not self.video_enabled or (camera_active and person_present)
