import unittest

from audio.detector import AudioDetector, MicrophoneDetector, build_detector as build_audio_detector
from core.config import AudioConfig, RFConfig, VisionConfig
from rf.detector import HackRFDetector, RFDetector, build_detector as build_rf_detector
from vision.detector import RTSPVisionDetector, VisionDetector, build_detector as build_vision_detector


class BackendSelectionTests(unittest.TestCase):
    def test_rf_defaults_to_simulation_backend(self):
        detector = build_rf_detector(RFConfig(simulation_mode=True, backend="simulation"))
        self.assertIsInstance(detector, RFDetector)

    def test_rf_real_backend_selection(self):
        detector = build_rf_detector(RFConfig(simulation_mode=False, backend="real"))
        self.assertIsInstance(detector, HackRFDetector)

    def test_audio_defaults_to_simulation_backend(self):
        detector = build_audio_detector(AudioConfig(simulation_mode=True, backend="simulation"))
        self.assertIsInstance(detector, AudioDetector)

    def test_audio_real_backend_selection(self):
        detector = build_audio_detector(AudioConfig(simulation_mode=False, backend="real"))
        self.assertIsInstance(detector, MicrophoneDetector)

    def test_vision_defaults_to_simulation_backend(self):
        detector = build_vision_detector(VisionConfig(simulation_mode=True, backend="simulation"))
        self.assertIsInstance(detector, VisionDetector)

    def test_vision_real_backend_selection(self):
        detector = build_vision_detector(VisionConfig(simulation_mode=False, backend="real"))
        self.assertIsInstance(detector, RTSPVisionDetector)


if __name__ == "__main__":
    unittest.main()
