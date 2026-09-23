# 🌙 EchoNode: Standalone Bedside Audio Player

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hardware: ESP32-S3](https://img.shields.io/badge/Hardware-Waveshare%20ESP32--S3%201.85%22%20Round-blue.svg)](https://www.waveshare.com)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20yt--dlp-009688.svg)](https://fastapi.tiangolo.com)
[![UI: LVGL](https://img.shields.io/badge/UI-LVGL%208.3.11-brightgreen.svg)](https://lvgl.io)

**EchoNode** is an open-source, dedicated hardware bedside audio device designed to solve a critical real-world problem: **preventing mobile phone dependency, eliminating cellular RF radiation, and silencing disruptive notifications right before and during sleep cycles.**

Built around the **Waveshare ESP32-S3 1.85-inch Circular Display Development Board**, EchoNode delivers a zero-notification, dedicated bedside audio experience with dual operating profiles and a local web ingestion service.

---

## ⚡ Core Features

- 🎧 **Standalone SD Mode (Zero Radio):** Reads audio-only `.m4a` (AAC) or `.mp3` tracks directly from a FAT32 MicroSD card. Wi-Fi and Bluetooth baseband registers are powered off completely to maximize battery life and eliminate radiation.
- 📶 **Bluetooth A2DP Sink Mode:** Transforms the unit into a high-fidelity wireless bedside speaker for paired smartphones when desired.
- 🔄 **Strict Mutual Exclusion:** Memory allocations for SD playback and Bluetooth A2DP never run in RAM simultaneously, preventing crashes and memory leaks.
- 🛡️ **Built-in Safety Policies:**
  - `RULE_VOLUME_CEILING`: Digital volume hard-capped at 65% to prevent coil distortion and brownout voltage sags.
  - `RULE_I2S_MUTING`: Automatic hardware mute on stop/pause to silence all ambient hiss and high-frequency EMI.
  - `RULE_THERMAL_SHUTDOWN`: 30-minute idle sleep timeout prevents heat entrapment near bedding and pillows.
  - 10-second automatic screen backlight dimming for pitch-black sleep environments.
- 🌐 **Web Ingestion Hub:** FastAPI + `yt-dlp` local backend service that takes YouTube links, strips heavy video tracks, and formats them into clean, audio-only `.m4a` files with FAT32-safe filenames for MicroSD transfer.
- 🎨 **Circular LVGL User Interface:** Custom UI tailored for the 360×360 round display (Screen Alpha: Clock/Battery/Mode, Screen Beta: 1Hz SD Player, Screen Gamma: Bluetooth Discovery).

---

## 📁 Repository Structure

```
EchoNode/
├── backend/                  # FastAPI web service & yt-dlp audio extractor
│   ├── app/                  # Application routes, models, config, and extractor service
│   ├── static/               # Modern dark-mode web dashboard UI
│   ├── tests/                # Unit tests & live extraction verification
│   ├── downloads/            # Staged audio files ready for SD transfer
│   └── requirements.txt      # Python dependencies
├── firmware/                 # Production firmware for Waveshare ESP32-S3 Round LCD
│   ├── include/              # Hardware pinouts, LVGL config, and subsystem headers
│   ├── src/                  # Audio manager, display manager, power manager, SD manager
│   ├── platformio.ini        # PlatformIO build configuration (16MB Flash, 8MB PSRAM OPI)
│   └── partitions_16MB.csv   # Custom flash partition table
├── ARCHITECTURE.md           # System topology and operational matrix
├── DESIGN.md                 # LVGL UI guidelines and screen coordinate maps
├── MEMORY.md                 # Flash partitioning and PSRAM/SRAM allocation rules
├── PDR.md                    # Product Design Requirements specification
├── RULES.md                  # Safety directives and firmware policies
└── TASK.md                   # Project engineering task roadmap
```

---

## 🚀 Quickstart Guide

### 1. Web Ingestion Hub (Audio Extractor)

The backend extracts audio streams from YouTube and stages them for MicroSD transfer:

```bash
# Navigate to backend directory
cd backend

# Initialize virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run backend server
python run.py
```

Open your browser at **`http://localhost:8000`** to access the EchoNode Audio Hub dashboard. Paste any YouTube link to extract audio-only M4A files or sync directly to a connected MicroSD card.

### 2. Flashing the ESP32-S3 Firmware

```bash
# Navigate to firmware directory
cd firmware

# Build and upload using PlatformIO
pio run --target upload

# Launch serial monitor at 115200 baud
pio run --target monitor
```

---

## ⚠️ Hardware Safety Directives

* **`RULE_POLARITY_CHECK`:** Before connecting any battery to the board's MX1.25 connector, verify the positive and negative leads against the PCB silkscreen with a multimeter. Swapped polarity will destroy the onboard charging IC.
* **MicroSD Requirements:** Use cards $\le 32\text{GB}$ formatted as **FAT32**.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
