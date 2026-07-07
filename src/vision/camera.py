"""OpenCV camera discovery and preview helpers."""

from __future__ import annotations

import cv2

from src.utils.logger import log


def get_available_cameras(max_index: int = 5) -> list[int]:
    """Return camera indexes that can be opened and read by OpenCV."""
    cameras: list[int] = []
    for index in range(max_index):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                cameras.append(index)
            cap.release()
    return cameras


def test_camera(index: int) -> bool:
    """Show a preview window for the selected camera until the user presses Q."""
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        log("Failed to open camera.")
        return False

    log("Press Q to close preview window.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow(f"Camera Test - Index {index}", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return True
