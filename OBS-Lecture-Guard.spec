# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

import mediapipe as mp


project_root = Path.cwd()
icon_path = project_root / "assets" / "app.ico"
mediapipe_modules = Path(mp.__file__).parent / "modules"


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(mediapipe_modules), "mediapipe/modules"),
    ],
    hiddenimports=[
        "mediapipe",
        "mediapipe.python.solutions.pose",
        "mediapipe.python.solutions.drawing_utils",
        "google.protobuf",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="OBS-Lecture-Guard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
