from __future__ import annotations

from collections import deque
from threading import Lock

from core.models import DetectionEvent


class EventBus:
    def __init__(self, history_limit: int = 200):
        self._events: deque[DetectionEvent] = deque(maxlen=history_limit)
        self._lock = Lock()

    def publish(self, event: DetectionEvent) -> None:
        with self._lock:
            self._events.appendleft(event)

    def list_events(self, limit: int | None = None) -> list[DetectionEvent]:
        with self._lock:
            events = list(self._events)
        if limit is None:
            return events
        return events[:limit]

    def latest_event(self) -> DetectionEvent | None:
        with self._lock:
            return self._events[0] if self._events else None

