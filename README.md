# OBS Lecture Guard

OBS Lecture Guard is a Python console application that monitors OBS Studio during lecture recording. It warns when the configured microphone is muted while teaching, when audio stays silent for too long, and when the presenter enters or leaves the camera frame.

The project started as a working single-file console tool and was later refactored into a modular architecture.

## Features

- Connects to OBS Studio through `obsws-python`
- Supports OBS WebSocket host, port, and password configuration
- Retries OBS connection when OBS is unavailable or disconnects
- Detects recording start and stop state
- Reads available OBS inputs during first-run setup
- Monitors the selected microphone mute state and volume level
- Detects long silence using OBS input volume in dB
- Uses OpenCV and MediaPipe in a background thread for presenter detection
- Checks whether the configured camera source is enabled in the current OBS scene
- Checks whether OBS Virtual Camera is active before treating video detection as active
- Prints console alerts and plays Windows beep notifications
- Opens a separate debug control console for debug preview on/off and whole-app exit
- Handles `KeyboardInterrupt` gracefully

## Architecture

```text
main.py
src/
  config/manager.py      # config loading, validation, first-run setup
  obs/client.py          # OBS WebSocket connection and safe API wrapper
  obs/monitor.py         # main monitoring loop coordination
  vision/camera.py       # camera scan and preview utilities
  vision/detector.py     # MediaPipe pose detector background thread
  audio/monitor.py       # microphone mute and silence state tracking
  alerts/notifier.py     # Windows beep notifications
  utils/logger.py        # simple console logging
```

The original shipped implementation remains in `legacy/` for reference and should not be modified.

## Requirements

- Windows
- Python 3.10, 3.11, or 3.12
- OBS Studio with OBS WebSocket enabled
- A working camera and microphone configured in OBS

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Use a Python 3.10-3.12 virtual environment for MediaPipe. The shipped-compatible environment used MediaPipe `0.10.14`; some Python 3.13 MediaPipe builds expose only the newer Tasks API and do not include the legacy `solutions.pose` API that this console tool uses.

## OBS Setup

1. Open OBS Studio.
2. Go to `Tools > WebSocket Server Settings`.
3. In Plugin Settings, enable WebSocket server.
4. In Server Settings, keep the default port unless you changed it. Use the same port when the app asks.
5. Enable authentication.
6. Set a password.
7. Click Show Connect Info.
8. If OBS asks whether it is currently live, click Yes.
9. Copy the password.
10. Close that dialog, then click Apply and OK.
11. Add/setup the microphone and camera sources you want to monitor in OBS.
12. Start OBS Virtual Camera if your monitoring flow depends on it.

When the app starts, it asks you to press Space after OBS is open and setup is ready. You can press `Ctrl+C` to exit safely at any step.

## Running From Source

Run:

```powershell
python main.py
```

On first run, the setup wizard creates `config.json`. The wizard asks for OBS connection details, lists OBS inputs, asks you to choose the microphone and camera source, scans local camera indexes, previews the selected camera, and saves the configuration.

`config.json` is a runtime file and is ignored by Git.

## Building an Executable

Install PyInstaller, then build a console executable:

```powershell
pyinstaller --onefile --console main.py
```

MediaPipe may require bundling its module data depending on the local environment. The legacy `legacy/main.spec` shows the previous shipped packaging approach and can be used as a reference when creating a production spec file.
