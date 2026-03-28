from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from threading import Lock

from audio.detector import build_detector as build_audio_detector
from core.config import AppConfig
from core.event_bus import EventBus
from core.models import DetectionEvent, DetectionReading, Severity
from rf.detector import build_detector as build_rf_detector
from vision.detector import build_detector as build_vision_detector


@dataclass(slots=True)
class ModuleStatus:
    name: str
    enabled: bool
    simulation_mode: bool
    interval_seconds: float
    backend: str
    last_reading: dict | None = None


class DetectionEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.event_bus = EventBus(history_limit=config.history_limit)
        self._event_counter = count(1)
        self._status_lock = Lock()
        self._statuses: dict[str, ModuleStatus] = {
            "rf": ModuleStatus(
                "rf",
                config.rf.enabled,
                config.rf.simulation_mode,
                config.rf.interval_seconds,
                config.rf.backend,
            ),
            "audio": ModuleStatus(
                "audio",
                config.audio.enabled,
                config.audio.simulation_mode,
                config.audio.interval_seconds,
                config.audio.backend,
            ),
            "vision": ModuleStatus(
                "vision",
                config.vision.enabled,
                config.vision.simulation_mode,
                config.vision.interval_seconds,
                config.vision.backend,
            ),
        }
        self.detectors = []

        if config.rf.enabled:
            self.detectors.append(build_rf_detector(config.rf))
        if config.audio.enabled:
            self.detectors.append(build_audio_detector(config.audio))
        if config.vision.enabled:
            self.detectors.append(build_vision_detector(config.vision))

    def start(self) -> None:
        for detector in self.detectors:
            detector.start(self.process_reading)

    def stop(self) -> None:
        for detector in self.detectors:
            detector.stop()

    def process_reading(self, reading: DetectionReading) -> None:
        with self._status_lock:
            self._statuses[reading.source].last_reading = reading.to_dict()

        if not reading.detected:
            return

        severity = self._severity_from_confidence(reading.confidence)
        event = DetectionEvent(
            event_id=next(self._event_counter),
            title=f"{reading.source.upper()} module reported a drone signature",
            severity=severity,
            reading=reading,
        )
        self.event_bus.publish(event)

    def _severity_from_confidence(self, confidence: float) -> Severity:
        if confidence >= 0.85:
            return Severity.critical
        if confidence >= 0.65:
            return Severity.warning
        return Severity.info

    def get_status(self) -> dict:
        with self._status_lock:
            modules = {
                name: {
                    "name": status.name,
                    "enabled": status.enabled,
                    "simulation_mode": status.simulation_mode,
                    "interval_seconds": status.interval_seconds,
                    "backend": status.backend,
                    "last_reading": status.last_reading,
                }
                for name, status in self._statuses.items()
            }

        latest = self.event_bus.latest_event()
        return {
            "modules": modules,
            "events_recorded": len(self.event_bus.list_events()),
            "latest_event": latest.to_dict() if latest else None,
        }

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        return [event.to_dict() for event in self.event_bus.list_events(limit=limit)]
