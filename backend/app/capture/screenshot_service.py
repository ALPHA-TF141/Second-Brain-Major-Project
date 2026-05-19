from datetime import datetime
from hashlib import sha1
from pathlib import Path

import cv2
import mss
import numpy as np


class ScreenshotService:
    def __init__(self, storage_root: str = "data/screenshots"):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.last_hash = ""

    def capture(self, session_id: int):
        session_dir = self.storage_root / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        with mss.mss() as screen_capture:
            monitor = screen_capture.monitors[1]
            raw = screen_capture.grab(monitor)

        frame = np.array(raw)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        height, width = frame.shape[:2]

        max_width = 1280
        if width > max_width:
            scale = max_width / width
            frame = cv2.resize(frame, (max_width, int(height * scale)), interpolation=cv2.INTER_AREA)
            height, width = frame.shape[:2]

        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not ok:
            return None

        image_bytes = encoded.tobytes()
        image_hash = sha1(image_bytes).hexdigest()
        if image_hash == self.last_hash:
            return None

        self.last_hash = image_hash
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = session_dir / filename
        file_path.write_bytes(image_bytes)

        return {
            "file_path": str(file_path),
            "image_hash": image_hash,
            "width": width,
            "height": height,
        }
