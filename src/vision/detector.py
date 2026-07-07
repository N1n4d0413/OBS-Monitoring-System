"""Background MediaPipe pose detection for presenter presence."""

from __future__ import annotations

import os
import sys
import threading
import time
import warnings
from importlib import import_module
from typing import Any

import cv2

from src.utils.logger import log

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
warnings.filterwarnings("ignore", category=UserWarning)


class _DevNull:
    def write(self, msg: str) -> None:
        pass

    def flush(self) -> None:
        pass


_original_stderr = sys.stderr
try:
    sys.stderr = _DevNull()
    import mediapipe as mp  # noqa: E402
finally:
    sys.stderr = _original_stderr


def _load_mediapipe_solutions() -> tuple[Any, Any]:
    """Load the classic MediaPipe Solutions API used by the legacy app."""
    if hasattr(mp, "solutions"):
        return mp.solutions.pose, mp.solutions.drawing_utils

    try:
        pose = import_module("mediapipe.solutions.pose")
        drawing_utils = import_module("mediapipe.solutions.drawing_utils")
        return pose, drawing_utils
    except ModuleNotFoundError as error:
        version = getattr(mp, "__version__", "unknown")
        raise RuntimeError(
            "This MediaPipe install does not include the legacy "
            f"'solutions.pose' API required by this app (detected version: {version}). "
            "Install the requirements in a Python 3.10-3.12 virtual environment so "
            "MediaPipe includes Solutions support."
        ) from error


class PoseDetector:
    """Run camera processing in a daemon thread and track person presence."""

    def __init__(self, config: dict[str, Any], enabled: bool = True, debug: bool = False) -> None:
        self.config = config
        self.enabled = enabled
        self.debug = debug
        self.person_present = False
        self.previous_person_state: bool | None = None
        self.last_video_check = 0.0
        self.camera_active = False
        self.previous_camera_active: bool | None = None
        self._debug_window_open = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start pose detection in the background when video is enabled."""
        if not self.enabled:
            return
        self._thread = threading.Thread(target=self._video_monitor, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Request the detector thread to stop."""
        self._stop_event.set()
        self._close_debug_window()
        cv2.destroyAllWindows()

    def set_camera_active(self, active: bool) -> None:
        """Update whether the OBS scene currently has the camera source enabled."""
        with self._lock:
            if active == self.previous_camera_active:
                self.camera_active = active
                return

            self.camera_active = active
            self.previous_camera_active = active

            if active:
                log("VIDEO: OBS camera output active. Person detection enabled.")
                return

            self.person_present = False
            self.previous_person_state = False
            log("VIDEO: Person not detected because OBS camera output is inactive.")

    def set_debug(self, enabled: bool) -> None:
        """Turn the OpenCV debug preview window on or off."""
        with self._lock:
            if self.debug == enabled:
                return
            self.debug = enabled
            state = "ON" if enabled else "OFF"
            log(f"Debug mode {state}.")

    def get_person_status(self) -> bool:
        """Return the most recent person-present state."""
        with self._lock:
            return self.person_present

    def reset_previous_person_state(self) -> None:
        """Reset transition logging state at recording start."""
        with self._lock:
            self.previous_person_state = None

    def _video_monitor(self) -> None:
        try:
            cam_index = self.config.get("camera_index")
            if cam_index is None:
                log("ERROR: No camera found.")
                return

            log(f"Using camera index: {cam_index}")
            cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                log("Failed to open selected camera.")
                cap.release()
                return

            mp_pose, mp_drawing = _load_mediapipe_solutions()

            with mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            ) as pose:
                log("Video monitoring active")
                results = None

                while not self._stop_event.is_set():
                    ret, frame = cap.read()
                    if not ret:
                        time.sleep(0.5)
                        continue

                    display_frame = cv2.resize(frame, (800, 450))
                    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    current_time = time.time()

                    if self._is_debug_enabled():
                        results = pose.process(rgb)
                        self._show_debug_frame(display_frame, results, mp_drawing, mp_pose)

                        if current_time - self.last_video_check >= 1:
                            if self._is_camera_active():
                                self._update_person_state(results.pose_landmarks is not None)
                            self.last_video_check = current_time
                        continue

                    if current_time - self.last_video_check >= 1:
                        if self._is_camera_active():
                            results = pose.process(rgb)
                            self._update_person_state(results.pose_landmarks is not None)
                        self.last_video_check = current_time

        except RuntimeError as error:
            log(f"Video monitoring unavailable: {error}")
        except Exception as error:
            log(f"Video thread crashed: {error}")
        finally:
            if "cap" in locals():
                cap.release()
            cv2.destroyAllWindows()

    def _is_camera_active(self) -> bool:
        with self._lock:
            return self.camera_active

    def _is_debug_enabled(self) -> bool:
        with self._lock:
            return self.debug

    def _update_person_state(self, person_present: bool) -> None:
        with self._lock:
            self.person_present = person_present
            if self.previous_person_state is None:
                self.previous_person_state = person_present
                return

            if person_present == self.previous_person_state:
                return

            if person_present:
                log("VIDEO: Person detected.")
            else:
                log("VIDEO: Person left frame.")
            self.previous_person_state = person_present

    def _show_debug_frame(
        self,
        display_frame: Any,
        results: Any,
        mp_drawing: Any,
        mp_pose: Any,
    ) -> None:
        if not self._is_debug_enabled():
            self._close_debug_window()
            return

        self._ensure_debug_window()

        if results and results.pose_landmarks:
            mp_drawing.draw_landmarks(
                display_frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
            )

        pose_seen = bool(results and results.pose_landmarks)
        status_text = "MediaPipe: Person Detected" if pose_seen else "MediaPipe: No Person"
        color = (0, 255, 0) if pose_seen else (0, 0, 255)

        cv2.putText(
            display_frame,
            f"OpenCV input: camera index {self.config.get('camera_index')}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            display_frame,
            status_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            2,
        )
        cv2.imshow("MediaPipe Lecture Monitor", display_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.set_debug(False)

    def _ensure_debug_window(self) -> None:
        if self._debug_window_open:
            return

        cv2.namedWindow("MediaPipe Lecture Monitor", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("MediaPipe Lecture Monitor", 960, 540)
        cv2.moveWindow("MediaPipe Lecture Monitor", 80, 80)
        try:
            cv2.setWindowProperty(
                "MediaPipe Lecture Monitor",
                cv2.WND_PROP_TOPMOST,
                1,
            )
        except cv2.error:
            pass
        self._debug_window_open = True
        log("Debug MediaPipe window visible.")

    def _close_debug_window(self) -> None:
        if not self._debug_window_open:
            return

        try:
            cv2.destroyWindow("MediaPipe Lecture Monitor")
        except cv2.error:
            pass
        finally:
            self._debug_window_open = False
