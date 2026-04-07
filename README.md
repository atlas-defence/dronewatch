# DroneWatch

Open-source drone detection and tracking system using RF, audio, and visual signals.

- **Languages**: English (this page) · [Türkçe](README.tr.md)

---

## Screenshot

![DroneWatch dashboard screenshot](screenshot.png)

---

## Overview

DroneWatch is a modular monitoring system built around three sensor pipelines:

- RF scanning
- Acoustic detection
- Camera-based visual motion detection

The project now supports both simulation and real input workflows. Simulation remains the default so the app can boot without specialist hardware, but each module can be switched to a real backend independently.

---

## Current Backends

### RF

- `simulation`: seeded synthetic RF readings
- `real`: `hackrf_sweep` command integration for HackRF spectrum capture

### Audio

- `simulation`: seeded synthetic acoustic readings
- `real`: local microphone capture using `sounddevice`

### Vision

- `simulation`: seeded synthetic visual tracks
- `real`: RTSP IP camera ingest using OpenCV background subtraction and motion heuristics

---

## Important Scope Note

The real backends are operational ingestion paths, not military-grade drone classifiers.

- HackRF mode detects elevated RF energy in the configured band
- Microphone mode detects rotor-like tonal energy using amplitude and FFT heuristics
- RTSP mode detects moving visual targets using motion segmentation

These are real workflows and real device integrations, but they still use heuristic detection logic. They should be treated as an engineering baseline for field testing and iteration, not as a finished production detection stack.

---

## Hardware Support

- HackRF with `hackrf_sweep` installed and available on `PATH`
- Built-in or USB microphone supported by PortAudio / `sounddevice`
- RTSP IP camera reachable from the host machine

---

## Requirements

- Python 3.10+
- HackRF tools installed for RF real mode
- PortAudio-compatible audio input for microphone real mode
- OpenCV-compatible environment for RTSP real mode

Install Python packages:

```bash
pip install -r requirements.txt
```

---

## Run

```bash
python main.py
```

By default, all modules run in simulation mode.

---

## Configuration

Each sensor can be enabled, disabled, or switched between simulation and real mode with environment variables.

### RF real mode

```bash
DRONEWATCH_RF_SIMULATION=false
DRONEWATCH_RF_BACKEND=real
DRONEWATCH_RF_HACKRF_SWEEP_PATH=hackrf_sweep
DRONEWATCH_RF_START_MHZ=2400
DRONEWATCH_RF_STOP_MHZ=2485
DRONEWATCH_RF_BIN_WIDTH_HZ=1000000
DRONEWATCH_RF_SIGNAL_THRESHOLD_DB=-55
```

### Audio real mode

```bash
DRONEWATCH_AUDIO_SIMULATION=false
DRONEWATCH_AUDIO_BACKEND=real
DRONEWATCH_AUDIO_INPUT_DEVICE=
DRONEWATCH_AUDIO_SAMPLE_RATE=48000
DRONEWATCH_AUDIO_CAPTURE_SECONDS=1.5
DRONEWATCH_AUDIO_AMPLITUDE_THRESHOLD=0.03
DRONEWATCH_AUDIO_BAND_MIN_HZ=120
DRONEWATCH_AUDIO_BAND_MAX_HZ=700
```

Leave `DRONEWATCH_AUDIO_INPUT_DEVICE` empty to use the default built-in microphone.

### Vision real mode

```bash
DRONEWATCH_VISION_SIMULATION=false
DRONEWATCH_VISION_BACKEND=real
DRONEWATCH_VISION_RTSP_URL=rtsp://user:password@camera-ip:554/stream
DRONEWATCH_VISION_CAMERA_ID=cam-01
DRONEWATCH_VISION_FRAME_WIDTH=960
DRONEWATCH_VISION_MIN_MOTION_AREA=1400
```

### Mixed-mode example

This keeps audio simulated while RF and vision use real hardware:

```bash
DRONEWATCH_RF_SIMULATION=false
DRONEWATCH_RF_BACKEND=real
DRONEWATCH_AUDIO_SIMULATION=true
DRONEWATCH_VISION_SIMULATION=false
DRONEWATCH_VISION_BACKEND=real
DRONEWATCH_VISION_RTSP_URL=rtsp://user:password@camera-ip:554/stream
```

---

## Modules

- `rf/`: RF scanning and HackRF integration
- `audio/`: simulation and live microphone ingestion
- `vision/`: simulation and RTSP camera ingestion
- `core/`: engine, models, and configuration
- `api/`: dashboard and JSON APIs

---

## Validation Notes

If a real backend cannot initialize, the module stays alive and reports a non-detected reading with an explanatory error message. This lets the dashboard stay online while showing which dependency or device is missing.

---

## License

MIT License
