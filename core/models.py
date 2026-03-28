from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


@dataclass(slots=True)
class DetectionReading:
    source: str
    confidence: float
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    detected: bool = True
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


@dataclass(slots=True)
class DetectionEvent:
    event_id: int
    title: str
    severity: Severity
    reading: DetectionReading
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "severity": self.severity.value,
            "reading": self.reading.to_dict(),
            "created_at": self.created_at.isoformat(),
        }

