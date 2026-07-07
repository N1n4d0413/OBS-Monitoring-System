"""Safe OBS WebSocket client wrapper with reconnect support."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

import obsws_python as obs
from obsws_python.error import OBSSDKRequestError

from src.utils.logger import log

logging.getLogger("websocket").setLevel(logging.CRITICAL)

T = TypeVar("T")


class OBSClient:
    """Create and maintain an OBS WebSocket request client."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.host = config.get("host")
        self.port = config.get("port")
        self.password = config.get("password")
        self.client: obs.ReqClient | None = None
        self._virtual_camera_status_supported = True
        self.connect()

    def connect(self) -> obs.ReqClient:
        """Connect to OBS, retrying until OBS becomes available."""
        while True:
            try:
                self.client = obs.ReqClient(
                    host=self.host,
                    port=int(self.port),
                    password=self.password,
                )
                log("Connected to OBS.")
                return self.client
            except Exception:
                log("OBS not running. Retrying in 5 seconds...")
                time.sleep(5)

    def safe_call(self, method_name: str, *args: Any) -> Any | None:
        """Call an OBS API method and reconnect on transient failures."""
        try:
            if self.client is None:
                self.connect()
            method: Callable[..., T] = getattr(self.client, method_name)
            return method(*args)
        except OBSSDKRequestError:
            time.sleep(1)
            return None
        except (ConnectionResetError, ConnectionRefusedError, OSError):
            log("OBS disconnected. Reconnecting...")
            time.sleep(1)
            self.connect()
            return None
        except Exception:
            log("OBS error. Reconnecting...")
            time.sleep(1)
            self.connect()
            return None

    def get_record_status(self) -> Any | None:
        """Return OBS recording status, or None if OBS is not ready."""
        return self.safe_call("get_record_status")

    def get_input_mute(self, input_name: str) -> Any | None:
        """Return mute state for an OBS input."""
        return self.safe_call("get_input_mute", input_name)

    def get_input_volume(self, input_name: str) -> Any | None:
        """Return volume information for an OBS input."""
        return self.safe_call("get_input_volume", input_name)

    def is_virtual_camera_active(self) -> bool:
        """Return True when OBS Virtual Camera output is active."""
        if not self._virtual_camera_status_supported:
            return False

        if self.client is not None and not hasattr(self.client, "get_virtual_cam_status"):
            self._virtual_camera_status_supported = False
            log("OBS Virtual Camera status is not supported by this obsws-python version.")
            return False

        status = self.safe_call("get_virtual_cam_status")
        if status is None:
            return False
        return bool(getattr(status, "output_active", False))

    def is_camera_enabled(self, camera_source: str) -> bool:
        """Return True when the configured source is enabled in the program scene."""
        try:
            if self.client is None:
                self.connect()

            scene = self.client.get_current_program_scene().current_program_scene_name
            items = self.client.get_scene_item_list(scene).scene_items

            for item in items:
                if item["sourceName"] == camera_source:
                    scene_item_id = item["sceneItemId"]
                    enabled = self.client.get_scene_item_enabled(
                        scene,
                        scene_item_id,
                    ).scene_item_enabled
                    return bool(enabled)

            return False
        except Exception:
            return False
