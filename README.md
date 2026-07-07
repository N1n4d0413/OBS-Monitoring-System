# OBS Lecture Guard

OBS Lecture Guard is a Windows console application for monitoring OBS Studio during lecture recordings. It watches the selected OBS microphone, camera source, OBS Virtual Camera state, and live camera feed so it can warn when the presenter is visible but the microphone is muted or silent.

The project started as a working single-file console tool and was later refactored into a maintainable modular Python architecture.

## Features

- Connects to OBS Studio through `obsws-python`
- Supports OBS WebSocket host, port, and password setup
- Retries OBS connection if OBS is closed or temporarily unavailable
- Detects OBS recording start and stop
- First-run setup wizard for microphone, camera source, and camera index selection
- Checks OBS scene source visibility, capture device active state, and OBS Virtual Camera state separately
- Uses OpenCV and MediaPipe for live presenter/person detection
- Runs vision processing in a background thread
- Detects microphone mute state and long silence from OBS volume dB
- Shows console alerts and Windows beep notifications
- Optional debug control console for MediaPipe preview on/off and app exit
- Graceful `Ctrl+C` shutdown
- PyInstaller-compatible console EXE build

## Project Structure

```text
main.py
src/
  alerts/notifier.py     # Windows beep notifications
  audio/monitor.py       # mic mute and silence monitoring
  config/manager.py      # config loading, validation, setup wizard
  obs/client.py          # safe OBS WebSocket client wrapper
  obs/monitor.py         # main OBS monitoring loop
  utils/control.py       # debug control terminal
  utils/logger.py        # console logging helper
  utils/paths.py         # source vs EXE runtime paths
  vision/camera.py       # camera scan and preview helpers
  vision/detector.py     # OpenCV + MediaPipe background detector
assets/
  README.md              # local icon instructions
installer/
  OBS-Lecture-Guard.iss  # optional local Inno Setup installer template
```

## Requirements

- Windows
- Python 3.10, 3.11, or 3.12
- OBS Studio
- OBS WebSocket enabled in OBS
- Camera and microphone added as OBS sources

MediaPipe compatibility matters. This project is pinned to:

```text
mediapipe==0.10.14
```

Do not run the app with global Python 3.13 on this machine, because that MediaPipe build does not expose the legacy `mediapipe.solutions.pose` API used by this tool.

## Setup From Source

Create and activate a compatible virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run:

```powershell
python main.py
```

On this machine, the included launcher uses the known-compatible Python 3.11 environment:

```powershell
.\run_app.bat
```

## OBS WebSocket Setup

1. Open OBS Studio.
2. Go to `Tools > WebSocket Server Settings`.
3. In Plugin Settings, enable WebSocket server.
4. Keep the default port unless you changed it. Use the same port when the app asks.
5. Enable authentication.
6. Set a password.
7. Click `Show Connect Info`.
8. If OBS asks whether it is currently live, click `Yes`.
9. Copy the password.
10. Close the dialog, then click `Apply` and `OK`.
11. Add the microphone and camera sources you want to monitor in OBS.
12. Start OBS Virtual Camera if your monitoring flow depends on it.

When `config.json` does not exist, the app shows these setup steps before the wizard. If a saved config exists, the app skips the full setup text and tells you how to reset setup.

To reset setup, delete `config.json` and run the app again.

## Runtime Files

When running from source, runtime files are created in the project folder:

```text
config.json
app_control.json
```

When running as a packaged EXE, runtime files are written under:

```text
%APPDATA%\OBS Lecture Guard
```

Runtime files are ignored by Git.

## Debug Mode

The debug preview is OFF by default.

When enabled from the debug control console, it opens a MediaPipe/OpenCV window showing the actual live camera feed being processed. The window overlays whether MediaPipe sees a person and draws landmarks when detection succeeds.

## App Logo

Add your local Windows icon here:

```text
assets/app.ico
```

Use a square `.ico` file with common sizes such as 16, 32, 48, 128, and 256 px.

`assets/app.ico` is ignored by Git so you can keep the logo local while still keeping the build script ready.

## Build EXE Locally

The GitHub repo should contain source code and build instructions, not generated EXE files.

To build locally:

```powershell
.\build_exe.bat
```

The EXE will be created at:

```text
dist/OBS-Lecture-Guard.exe
```

PyInstaller bundles dependencies such as OpenCV, MediaPipe, and `obsws-python` into the EXE at build time. The app should not install Python packages when the user runs it.

## Optional Installer

After building the EXE, you can create a Windows installer with Inno Setup:

```text
installer/OBS-Lecture-Guard.iss
```

The installer template installs the already-built EXE and creates shortcuts. Installer output should stay local and is ignored by Git.
