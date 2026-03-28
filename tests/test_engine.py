import unittest

from core.config import AppConfig, DetectorConfig
from core.engine import DetectionEngine
from core.models import DetectionReading


class DetectionEngineTests(unittest.TestCase):
    def test_detected_reading_creates_event(self):
        config = AppConfig(
            rf=DetectorConfig(enabled=False),
            audio=DetectorConfig(enabled=False),
            vision=DetectorConfig(enabled=False),
        )
        engine = DetectionEngine(config)
        reading = DetectionReading(source="rf", confidence=0.91, message="test", detected=True)

        engine.process_reading(reading)

        events = engine.get_recent_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["severity"], "critical")

    def test_non_detected_reading_does_not_create_event(self):
        config = AppConfig(
            rf=DetectorConfig(enabled=False),
            audio=DetectorConfig(enabled=False),
            vision=DetectorConfig(enabled=False),
        )
        engine = DetectionEngine(config)
        reading = DetectionReading(source="audio", confidence=0.20, message="quiet", detected=False)

        engine.process_reading(reading)

        self.assertEqual(engine.get_recent_events(limit=10), [])


if __name__ == "__main__":
    unittest.main()
