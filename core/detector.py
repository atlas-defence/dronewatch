from __future__ import annotations

from abc import ABC, abstractmethod
from threading import Event, Thread
from time import sleep

from core.models import DetectionReading


class BaseDetector(ABC):
    def __init__(self, name: str, interval_seconds: float = 2.0):
        self.name = name
        self.interval_seconds = interval_seconds
        self._thread: Thread | None = None
        self._stop_event = Event()

    def start(self, callback):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, args=(callback,), name=f"{self.name}-detector", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self, callback):
        while not self._stop_event.is_set():
            reading = self.read()
            if reading is not None:
                callback(reading)
            sleep(self.interval_seconds)

    @abstractmethod
    def read(self) -> DetectionReading | None:
        raise NotImplementedError

