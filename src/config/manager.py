"""Configuration loading, validation, and first-run setup wizard."""

from __future__ import annotations

import json
import msvcrt
import os
import subprocess
from pathlib import Path
from typing import Any

import obsws_python as obs

from src.utils.logger import log
from src.vision.camera import get_available_cameras, test_camera


class ConfigManager:
    """Manage the runtime configuration file for the console application."""

    REQUIRED_KEYS = (
        "host",
        "port",
        "password",
        "mic_name",
        "camera_source",
        "camera_index",
    )

    def __init__(self, config_path: str | Path = "config.json") -> None:
        self.config_path = Path(config_path)

    def load(self) -> dict[str, Any]:
        """Load an existing config or create a new one through the setup wizard."""
        if self.config_path.exists():
            config = self._read_config()
            if self.validate(config):
                log("Using saved configuration from config.json.")
                log("To reset setup, delete config.json and restart the app.")
                self._wait_for_obs_process()
                return config

            log("Config missing required fields. Recreating config...")
            self._remove_invalid_config()

        self._wait_for_obs_ready()
        return self.create_wizard()

    def validate(self, config: Any) -> bool:
        """Return True when the loaded config contains all required fields."""
        return isinstance(config, dict) and all(key in config for key in self.REQUIRED_KEYS)

    def save(self, config: dict[str, Any]) -> None:
        """Persist configuration in the same runtime file used by the legacy app."""
        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(config, file)
        log("Configuration saved.")

    def create_wizard(self) -> dict[str, Any]:
        """Run the first-time setup wizard and return a valid configuration."""
        log("=== First Time Setup ===")
        self._confirm_device_setup()

        host = self._prompt_host()
        port_text = input("Enter OBS Port (default 4455): ") or "4455"
        password = input("Enter OBS Password: ")

        try:
            port = int(port_text)
            client = obs.ReqClient(host=host, port=port, password=password)
            log("Connected to OBS.")
        except Exception:
            log("Failed to connect to OBS. Check details.")
            raise SystemExit(1)

        inputs = client.get_input_list()
        mic_inputs, camera_sources = self._display_inputs(inputs.inputs)

        selected_mic = self._select_from_list(
            mic_inputs,
            "\nEnter number of mic input to monitor: ",
        )

        log("\nSelect Camera Source Used In OBS Scene:")
        for index, source in enumerate(camera_sources):
            log(f"{index}: {source}")

        selected_camera = self._select_from_list(
            camera_sources,
            "\nEnter number of camera source: ",
        )
        selected_cam_index = self._select_camera_index()

        config = {
            "host": host,
            "port": port,
            "password": password,
            "mic_name": selected_mic,
            "camera_source": selected_camera,
            "camera_index": selected_cam_index,
        }
        self.save(config)
        return config

    @staticmethod
    def _wait_for_obs_ready() -> None:
        ConfigManager._show_obs_setup_steps()
        log("After completing the steps above, press SPACE to continue.")
        log("You can press Ctrl+C to exit safely at any step.")
        ConfigManager._wait_for_obs_process()

    @staticmethod
    def _wait_for_obs_process() -> None:
        log("Open OBS Studio first, then press SPACE to continue.")
        while True:
            key = msvcrt.getch()
            if key == b" ":
                print()
                if ConfigManager._is_obs_running():
                    return
                log("OBS Studio does not seem to be running. Open OBS Studio, then press SPACE again.")
                continue
            log("Press SPACE after OBS Studio is open.")

    @staticmethod
    def _confirm_device_setup() -> None:
        log(
            "Now make sure the microphone and camera devices you want to monitor are "
            "added inside OBS. Only sources already added in OBS will appear in the "
            "selection list."
        )
        input("Press Enter to continue setup...")

    @staticmethod
    def _show_obs_setup_steps() -> None:
        log("OBS WebSocket setup:")
        log("1. Open OBS Studio.")
        log("2. Go to Tools > WebSocket Server Settings.")
        log("3. In Plugin Settings, enable WebSocket server.")
        log("4. In Server Settings, keep the default port unless you changed it.")
        log("5. Enable authentication.")
        log("6. Set a password.")
        log("7. Click Show Connect Info.")
        log("8. If OBS asks whether it is currently live, click Yes.")
        log("9. Copy the password.")
        log("10. Close that dialog, then click Apply and OK.")
        log("11. Add/setup the mic and camera sources you want to monitor in OBS.")

    @staticmethod
    def _prompt_host() -> str:
        host = input("Enter OBS Host (default: localhost): ").strip()
        if not host:
            log("Using default OBS Host: localhost")
            return "localhost"
        return host

    @staticmethod
    def _is_obs_running() -> bool:
        """Return True when an OBS Studio process is visible on Windows."""
        try:
            result = subprocess.run(
                ["tasklist"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return False

        processes = result.stdout.lower()
        return any(name in processes for name in ("obs64.exe", "obs32.exe", "obs.exe"))

    def _read_config(self) -> dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _remove_invalid_config(self) -> None:
        try:
            os.remove(self.config_path)
        except OSError:
            pass

    @staticmethod
    def _display_inputs(inputs: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
        log("\nAvailable Inputs:")
        mic_inputs: list[str] = []
        camera_sources: list[str] = []

        for index, input_item in enumerate(inputs):
            input_name = input_item["inputName"]
            input_kind = input_item["inputKind"]
            log(f"{index}: {input_name} | Type: {input_kind}")
            mic_inputs.append(input_name)
            camera_sources.append(input_name)

        return mic_inputs, camera_sources

    @staticmethod
    def _select_from_list(options: list[str], prompt: str) -> str:
        while True:
            try:
                choice = int(input(prompt))
                if 0 <= choice < len(options):
                    return options[choice]
            except Exception:
                pass
            log("Invalid selection. Try again.")

    @staticmethod
    def _select_camera_index() -> int:
        log("\nDetecting available camera indexes...")
        available_cams = get_available_cameras()

        if not available_cams:
            log("No cameras detected.")
            raise SystemExit(1)

        log("Available Camera Indexes:")
        for index in available_cams:
            log(f"- {index}")

        while True:
            try:
                cam_index = int(input("\nEnter camera index to use: "))
                if cam_index not in available_cams:
                    log("Invalid index.")
                    continue

                log("Testing selected camera...")
                test_camera(cam_index)

                confirm = input("Use this camera? (y/n): ").lower()
                if confirm == "y":
                    return cam_index
            except Exception:
                log("Invalid input.")
