from __future__ import annotations

from random import Random

from core.config import AudioConfig
from core.detector import BaseDetector
from core.models import DetectionReading

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - optional dependency
    sd = None


class AudioDetector(BaseDetector):
    def __init__(self, interval_seconds: float = 3.0):
        super().__init__(name="audio", interval_seconds=interval_seconds)
        self._rng = Random(1188)

    def read(self) -> DetectionReading:
        confidence = round(self._rng.uniform(0.35, 0.93), 2)
        detected = confidence >= 0.60
        dominant_frequency = round(self._rng.uniform(120.0, 480.0), 1)
        noise_floor = round(self._rng.uniform(28.0, 61.0), 1)
        message = (
            "Rotor acoustic pattern detected near microphone array"
            if detected
            else "Ambient audio profile remains below drone threshold"
        )
        return DetectionReading(
            source="audio",
            confidence=confidence,
            detected=detected,
            message=message,
            metadata={
                "dominant_frequency_hz": dominant_frequency,
                "noise_floor_db": noise_floor,
                "profile": self._rng.choice(["quadcopter", "hexcopter", "ambiguous"]),
                "backend": "simulation",
            },
        )


class MicrophoneDetector(BaseDetector):
    def __init__(self, config: AudioConfig):
        super().__init__(name="audio", interval_seconds=config.interval_seconds)
        self.config = config

    def read(self) -> DetectionReading:
        if np is None or sd is None:
            return DetectionReading(
                source="audio",
                confidence=0.0,
                detected=False,
                message="Audio backend unavailable: install numpy and sounddevice for microphone capture",
                metadata={"backend": "microphone", "error": "missing_dependency"},
            )

        frames = max(1, int(self.config.sample_rate * self.config.capture_seconds))
        try:
            capture = sd.rec(
                frames,
                samplerate=self.config.sample_rate,
                channels=1,
                dtype="float32",
                device=self.config.input_device,
                blocking=True,
            )
        except Exception as exc:  # pragma: no cover - device/runtime specific
            return DetectionReading(
                source="audio",
                confidence=0.0,
                detected=False,
                message=f"Microphone capture failed: {exc}",
                metadata={"backend": "microphone", "error": "capture_failed"},
            )

        waveform = np.squeeze(capture)
        if waveform.size == 0:
            return DetectionReading(
                source="audio",
                confidence=0.0,
                detected=False,
                message="Microphone returned an empty capture buffer",
                metadata={"backend": "microphone", "error": "empty_capture"},
            )

        rms = float(np.sqrt(np.mean(np.square(waveform))))
        spectrum = np.abs(np.fft.rfft(waveform))
        frequencies = np.fft.rfftfreq(waveform.size, d=1.0 / self.config.sample_rate)
        dominant_index = int(np.argmax(spectrum))
        dominant_frequency = float(frequencies[dominant_index]) if frequencies.size else 0.0

        in_band = self.config.drone_band_min_hz <= dominant_frequency <= self.config.drone_band_max_hz
        detected = rms >= self.config.amplitude_threshold and in_band
        amplitude_ratio = rms / max(self.config.amplitude_threshold, 1e-6)
        confidence = max(0.05, min(0.99, round((amplitude_ratio / 2.5) + (0.18 if in_band else 0.0), 2)))
        if not detected:
            confidence = min(confidence, 0.49)

        profile = self._profile_from_frequency(dominant_frequency)
        noise_floor_db = round(20 * np.log10(max(rms, 1e-6)) + 94, 1)
        message = (
            f"Microphone captured rotor-like tonal energy at {dominant_frequency:.1f} Hz"
            if detected
            else "Live microphone input remained below the configured drone threshold"
        )
        return DetectionReading(
            source="audio",
            confidence=confidence,
            detected=detected,
            message=message,
            metadata={
                "dominant_frequency_hz": round(dominant_frequency, 1),
                "noise_floor_db": noise_floor_db,
                "profile": profile,
                "rms_level": round(rms, 4),
                "device": self.config.input_device or "default",
                "backend": "microphone",
            },
        )

    def _profile_from_frequency(self, dominant_frequency: float) -> str:
        if dominant_frequency < 220:
            return "heavy-lift"
        if dominant_frequency < 420:
            return "quadcopter"
        return "high-rpm"


def build_detector(config: AudioConfig) -> BaseDetector:
    if config.backend == "real" or not config.simulation_mode:
        return MicrophoneDetector(config)
    return AudioDetector(interval_seconds=config.interval_seconds)
