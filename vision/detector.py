from __future__ import annotations

from random import Random
from time import monotonic

from core.config import VisionConfig
from core.detector import BaseDetector
from core.models import DetectionReading

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None


class VisionDetector(BaseDetector):
    def __init__(self, interval_seconds: float = 4.0):
        super().__init__(name="vision", interval_seconds=interval_seconds)
        self._rng = Random(9050)

    def read(self) -> DetectionReading:
        confidence = round(self._rng.uniform(0.30, 0.96), 2)
        detected = confidence >= 0.62
        bbox = {
            "x": self._rng.randint(10, 600),
            "y": self._rng.randint(10, 340),
            "w": self._rng.randint(20, 120),
            "h": self._rng.randint(20, 120),
        }
        message = (
            "Small airborne object track matched drone silhouette"
            if detected
            else "No stable airborne target detected in video frame"
        )
        return DetectionReading(
            source="vision",
            confidence=confidence,
            detected=detected,
            message=message,
            metadata={
                "bounding_box": bbox,
                "camera_id": "cam-01",
                "track_id": self._rng.randint(1000, 9999),
                "backend": "simulation",
            },
        )


class RTSPVisionDetector(BaseDetector):
    def __init__(self, config: VisionConfig):
        super().__init__(name="vision", interval_seconds=config.interval_seconds)
        self.config = config
        self._capture = None
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=250, varThreshold=36) if cv2 else None
        self._track_counter = 1000
        self._last_connect_attempt = 0.0

    def stop(self):
        super().stop()
        if self._capture is not None and cv2 is not None:
            self._capture.release()
            self._capture = None

    def read(self) -> DetectionReading:
        if cv2 is None:
            return DetectionReading(
                source="vision",
                confidence=0.0,
                detected=False,
                message="Vision backend unavailable: install opencv-python-headless for RTSP ingest",
                metadata={"backend": "rtsp", "error": "missing_dependency"},
            )
        if not self.config.rtsp_url:
            return DetectionReading(
                source="vision",
                confidence=0.0,
                detected=False,
                message="Vision backend unavailable: set DRONEWATCH_VISION_RTSP_URL for the IP camera stream",
                metadata={"backend": "rtsp", "error": "missing_rtsp_url"},
            )

        connection_error = self._ensure_capture()
        if connection_error:
            return DetectionReading(
                source="vision",
                confidence=0.0,
                detected=False,
                message=connection_error,
                metadata={"backend": "rtsp", "camera_id": self.config.camera_id, "error": "connection_failed"},
            )

        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._reset_capture()
            return DetectionReading(
                source="vision",
                confidence=0.0,
                detected=False,
                message="RTSP camera frame read failed; waiting for reconnect",
                metadata={"backend": "rtsp", "camera_id": self.config.camera_id, "error": "read_failed"},
            )

        frame = self._resize_frame(frame)
        fg_mask = self._bg_subtractor.apply(frame)
        _, threshold = cv2.threshold(fg_mask, 235, 255, cv2.THRESH_BINARY)
        threshold = cv2.medianBlur(threshold, 5)
        threshold = cv2.dilate(threshold, None, iterations=2)

        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidate = self._pick_candidate(contours)
        if candidate is None:
            return DetectionReading(
                source="vision",
                confidence=0.18,
                detected=False,
                message="RTSP feed active but no airborne motion candidate passed the configured threshold",
                metadata={"backend": "rtsp", "camera_id": self.config.camera_id},
            )

        x, y, w, h, area = candidate
        self._track_counter += 1
        frame_area = frame.shape[0] * frame.shape[1]
        confidence = max(0.35, min(0.96, round(area / max(frame_area * 0.025, 1), 2)))
        return DetectionReading(
            source="vision",
            confidence=confidence,
            detected=True,
            message="RTSP camera detected a moving visual target that matches the configured motion profile",
            metadata={
                "bounding_box": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "camera_id": self.config.camera_id,
                "track_id": self._track_counter,
                "motion_area": int(area),
                "backend": "rtsp",
            },
        )

    def _ensure_capture(self) -> str | None:
        if self._capture is not None and self._capture.isOpened():
            return None

        now = monotonic()
        if now - self._last_connect_attempt < self.config.reconnect_cooldown_seconds:
            return "RTSP reconnect cooldown active"

        self._last_connect_attempt = now
        self._reset_capture()
        self._capture = cv2.VideoCapture(self.config.rtsp_url)
        if not self._capture.isOpened():
            self._reset_capture()
            return "Failed to open RTSP stream"
        return None

    def _pick_candidate(self, contours):
        best = None
        best_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.config.min_motion_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / max(h, 1)
            if aspect_ratio < 0.3 or aspect_ratio > 4.5:
                continue
            if area > best_area:
                best_area = area
                best = (x, y, w, h, area)
        return best

    def _resize_frame(self, frame):
        width = min(self.config.frame_width, frame.shape[1])
        if width <= 0 or width == frame.shape[1]:
            return frame
        ratio = width / frame.shape[1]
        height = max(1, int(frame.shape[0] * ratio))
        return cv2.resize(frame, (width, height))

    def _reset_capture(self):
        if self._capture is not None and cv2 is not None:
            self._capture.release()
        self._capture = None


def build_detector(config: VisionConfig) -> BaseDetector:
    if config.backend == "real" or not config.simulation_mode:
        return RTSPVisionDetector(config)
    return VisionDetector(interval_seconds=config.interval_seconds)
