from __future__ import annotations

import csv
import shutil
import subprocess
from io import StringIO
from random import Random

from core.config import RFConfig
from core.detector import BaseDetector
from core.models import DetectionReading


class RFDetector(BaseDetector):
    def __init__(self, interval_seconds: float = 2.0):
        super().__init__(name="rf", interval_seconds=interval_seconds)
        self._rng = Random(24058)

    def read(self) -> DetectionReading:
        confidence = round(self._rng.uniform(0.45, 0.97), 2)
        detected = confidence >= 0.58
        band = self._rng.choice(["2.4GHz", "5.8GHz"])
        signal_strength = round(self._rng.uniform(-72.0, -34.0), 1)
        vendor_hint = self._rng.choice(["unknown", "DJI-like", "custom telemetry", "consumer FPV"])
        message = (
            f"Detected probable drone RF activity on {band}"
            if detected
            else f"No significant drone RF signature on {band}"
        )
        return DetectionReading(
            source="rf",
            confidence=confidence,
            detected=detected,
            message=message,
            metadata={
                "band": band,
                "signal_strength_dbm": signal_strength,
                "vendor_hint": vendor_hint,
                "backend": "simulation",
            },
        )


class HackRFDetector(BaseDetector):
    def __init__(self, config: RFConfig):
        super().__init__(name="rf", interval_seconds=config.interval_seconds)
        self.config = config

    def read(self) -> DetectionReading:
        executable = shutil.which(self.config.hackrf_sweep_path) or self.config.hackrf_sweep_path
        if shutil.which(executable) is None and executable == self.config.hackrf_sweep_path:
            return DetectionReading(
                source="rf",
                confidence=0.0,
                detected=False,
                message="HackRF backend unavailable: hackrf_sweep was not found on PATH",
                metadata={"backend": "hackrf", "error": "command_not_found"},
            )

        command = [
            executable,
            "-f",
            f"{self.config.frequency_start_mhz}:{self.config.frequency_stop_mhz}",
            "-w",
            str(self.config.bin_width_hz),
            "-N",
            "1",
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return DetectionReading(
                source="rf",
                confidence=0.0,
                detected=False,
                message="HackRF sweep timed out before telemetry was returned",
                metadata={"backend": "hackrf", "error": "timeout"},
            )
        except OSError as exc:
            return DetectionReading(
                source="rf",
                confidence=0.0,
                detected=False,
                message=f"HackRF sweep failed to start: {exc}",
                metadata={"backend": "hackrf", "error": "startup_failure"},
            )

        if result.returncode != 0:
            error_text = (result.stderr or result.stdout).strip() or f"exit code {result.returncode}"
            return DetectionReading(
                source="rf",
                confidence=0.0,
                detected=False,
                message=f"HackRF sweep error: {error_text}",
                metadata={"backend": "hackrf", "error": "command_failed"},
            )

        parsed = self._parse_sweep_output(result.stdout)
        if parsed is None:
            return DetectionReading(
                source="rf",
                confidence=0.05,
                detected=False,
                message="HackRF returned data, but no usable sweep bins were parsed",
                metadata={"backend": "hackrf", "error": "parse_failed"},
            )

        max_db = parsed["max_db"]
        avg_db = parsed["avg_db"]
        strongest_freq_mhz = parsed["strongest_freq_mhz"]
        band = "2.4GHz" if strongest_freq_mhz < 3000 else "5.8GHz"
        margin = max_db - self.config.signal_threshold_db
        detected = max_db >= self.config.signal_threshold_db
        confidence = max(0.05, min(0.99, round(0.5 + (margin / 30.0), 2))) if detected else max(
            0.01, min(0.45, round(0.35 + (margin / 50.0), 2))
        )
        vendor_hint = "telemetry-like" if strongest_freq_mhz < 3000 else "fpv-like"
        message = (
            f"HackRF captured elevated RF energy near {strongest_freq_mhz:.3f} MHz"
            if detected
            else f"RF energy remained below threshold across {self.config.frequency_start_mhz}-{self.config.frequency_stop_mhz} MHz"
        )
        return DetectionReading(
            source="rf",
            confidence=confidence,
            detected=detected,
            message=message,
            metadata={
                "band": band,
                "signal_strength_dbm": round(max_db, 1),
                "average_power_dbm": round(avg_db, 1),
                "strongest_frequency_mhz": round(strongest_freq_mhz, 3),
                "vendor_hint": vendor_hint,
                "backend": "hackrf",
            },
        )

    def _parse_sweep_output(self, output: str) -> dict[str, float] | None:
        strongest_db = None
        strongest_freq_hz = None
        all_values: list[float] = []
        reader = csv.reader(StringIO(output))
        for row in reader:
            if len(row) < 7:
                continue
            try:
                hz_low = float(row[2])
                hz_high = float(row[3])
                step = float(row[4])
                power_values = [float(value) for value in row[6:] if value.strip()]
            except (TypeError, ValueError):
                continue

            if not power_values:
                continue

            all_values.extend(power_values)
            for index, power in enumerate(power_values):
                frequency = min(hz_high, hz_low + (index * step))
                if strongest_db is None or power > strongest_db:
                    strongest_db = power
                    strongest_freq_hz = frequency

        if strongest_db is None or strongest_freq_hz is None or not all_values:
            return None

        avg_db = sum(all_values) / len(all_values)
        return {
            "max_db": strongest_db,
            "avg_db": avg_db,
            "strongest_freq_mhz": strongest_freq_hz / 1_000_000.0,
        }


def build_detector(config: RFConfig) -> BaseDetector:
    if config.backend == "real" or not config.simulation_mode:
        return HackRFDetector(config)
    return RFDetector(interval_seconds=config.interval_seconds)
