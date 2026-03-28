from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _str_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip() or default


def _backend_env(prefix: str, simulation_mode: bool) -> str:
    explicit = _str_env(f"{prefix}_BACKEND")
    if explicit:
        return explicit.lower()
    return "simulation" if simulation_mode else "real"


@dataclass(slots=True)
class DetectorConfig:
    enabled: bool = True
    simulation_mode: bool = True
    interval_seconds: float = 2.0
    backend: str = "simulation"


@dataclass(slots=True)
class RFConfig(DetectorConfig):
    hackrf_sweep_path: str = "hackrf_sweep"
    frequency_start_mhz: int = 2400
    frequency_stop_mhz: int = 2485
    bin_width_hz: int = 1_000_000
    signal_threshold_db: float = -55.0
    command_timeout_seconds: float = 12.0


@dataclass(slots=True)
class AudioConfig(DetectorConfig):
    input_device: str | None = None
    sample_rate: int = 48_000
    capture_seconds: float = 1.5
    amplitude_threshold: float = 0.03
    drone_band_min_hz: float = 120.0
    drone_band_max_hz: float = 700.0


@dataclass(slots=True)
class VisionConfig(DetectorConfig):
    rtsp_url: str | None = None
    camera_id: str = "cam-01"
    frame_width: int = 960
    min_motion_area: int = 1_400
    reconnect_cooldown_seconds: float = 5.0


@dataclass(slots=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 5000
    history_limit: int = 200
    rf: RFConfig = field(default_factory=lambda: RFConfig(interval_seconds=2.0))
    audio: AudioConfig = field(default_factory=lambda: AudioConfig(interval_seconds=3.0))
    vision: VisionConfig = field(default_factory=lambda: VisionConfig(interval_seconds=4.0))


def load_config() -> AppConfig:
    rf_simulation = _bool_env("DRONEWATCH_RF_SIMULATION", True)
    audio_simulation = _bool_env("DRONEWATCH_AUDIO_SIMULATION", True)
    vision_simulation = _bool_env("DRONEWATCH_VISION_SIMULATION", True)

    return AppConfig(
        host=os.getenv("DRONEWATCH_HOST", "127.0.0.1"),
        port=int(os.getenv("DRONEWATCH_PORT", "5000")),
        history_limit=int(os.getenv("DRONEWATCH_HISTORY_LIMIT", "200")),
        rf=RFConfig(
            enabled=_bool_env("DRONEWATCH_RF_ENABLED", True),
            simulation_mode=rf_simulation,
            interval_seconds=_float_env("DRONEWATCH_RF_INTERVAL", 2.0),
            backend=_backend_env("DRONEWATCH_RF", rf_simulation),
            hackrf_sweep_path=_str_env("DRONEWATCH_RF_HACKRF_SWEEP_PATH", "hackrf_sweep") or "hackrf_sweep",
            frequency_start_mhz=_int_env("DRONEWATCH_RF_START_MHZ", 2400),
            frequency_stop_mhz=_int_env("DRONEWATCH_RF_STOP_MHZ", 2485),
            bin_width_hz=_int_env("DRONEWATCH_RF_BIN_WIDTH_HZ", 1_000_000),
            signal_threshold_db=_float_env("DRONEWATCH_RF_SIGNAL_THRESHOLD_DB", -55.0),
            command_timeout_seconds=_float_env("DRONEWATCH_RF_TIMEOUT_SECONDS", 12.0),
        ),
        audio=AudioConfig(
            enabled=_bool_env("DRONEWATCH_AUDIO_ENABLED", True),
            simulation_mode=audio_simulation,
            interval_seconds=_float_env("DRONEWATCH_AUDIO_INTERVAL", 3.0),
            backend=_backend_env("DRONEWATCH_AUDIO", audio_simulation),
            input_device=_str_env("DRONEWATCH_AUDIO_INPUT_DEVICE"),
            sample_rate=_int_env("DRONEWATCH_AUDIO_SAMPLE_RATE", 48_000),
            capture_seconds=_float_env("DRONEWATCH_AUDIO_CAPTURE_SECONDS", 1.5),
            amplitude_threshold=_float_env("DRONEWATCH_AUDIO_AMPLITUDE_THRESHOLD", 0.03),
            drone_band_min_hz=_float_env("DRONEWATCH_AUDIO_BAND_MIN_HZ", 120.0),
            drone_band_max_hz=_float_env("DRONEWATCH_AUDIO_BAND_MAX_HZ", 700.0),
        ),
        vision=VisionConfig(
            enabled=_bool_env("DRONEWATCH_VISION_ENABLED", True),
            simulation_mode=vision_simulation,
            interval_seconds=_float_env("DRONEWATCH_VISION_INTERVAL", 4.0),
            backend=_backend_env("DRONEWATCH_VISION", vision_simulation),
            rtsp_url=_str_env("DRONEWATCH_VISION_RTSP_URL"),
            camera_id=_str_env("DRONEWATCH_VISION_CAMERA_ID", "cam-01") or "cam-01",
            frame_width=_int_env("DRONEWATCH_VISION_FRAME_WIDTH", 960),
            min_motion_area=_int_env("DRONEWATCH_VISION_MIN_MOTION_AREA", 1_400),
            reconnect_cooldown_seconds=_float_env("DRONEWATCH_VISION_RECONNECT_COOLDOWN", 5.0),
        ),
    )
