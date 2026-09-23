# System Architecture & Technical Topology

## 1. Dual Operational Profile Matrix & Hardware Capability Gating

```
┌────────────────────────────────────────────────────────┐
│               ESP32-S3 Firmware System                 │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────┴───────────────────────────┐
▼                                                       ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     Standalone SD Mode        │       │     Bluetooth Audio Mode      │
├───────────────────────────────┤       ├───────────────────────────────┤
│ • Wi-Fi / Bluetooth: OFF      │       │ • Capability-Gated Interface  │
│ • Reads M4A/MP3 from SD card  │       │ • ESP32-S3 lacks Classic BT   │
│ • Zero phone notifications    │       │ • Reports NOT_SUPPORTED       │
│ • Maximum battery savings     │       │ • Extensible for external copr│
│ • PCM5101 I2S Output          │       │ • Radios remain unpowered     │
└───────────────────────────────┘       └───────────────────────────────┘
```

## 2. Memory Mutual Exclusion Finite State Machine (FSM)

The firmware enforces strict resource mutual exclusion through a deterministic state machine:

```
               ┌───────────┐
               │    OFF    │◄────────────────────────┐
               └─────┬─────┘                         │
                     │                               │
        ┌────────────┴────────────┐                  │
        ▼                         ▼                  │
┌──────────────────┐     ┌──────────────────┐        │
│LOCAL_SD_STARTING │     │   BT_STARTING    │        │
└───────┬──────────┘     └────────┬─────────┘        │
        │                         │ (Unsupported on  │
        ▼                         │  ESP32-S3 SoC)   │
┌──────────────────┐              ▼                  │
│ LOCAL_SD_ACTIVE  │     ┌──────────────────┐        │
└───────┬──────────┘     │    BT_STOPPING   │────────┘
        │                └──────────────────┘
        ▼
┌──────────────────┐
│LOCAL_SD_STOPPING │─────────────────────────────────┘
└──────────────────┘
```

### Transition Guarantee:
`ACTIVE_A -> mute audio -> stop stream -> destroy decoder -> free heap/PSRAM -> clear pointers -> verify resources -> ACTIVE_B`

* No global `Audio` object.
* No static instances of decoders.
* Explicit heap and PSRAM accounting before allocation and after destruction to prevent memory fragmentation and leaks.

## 3. Subsystem Breakdowns

### A. Web Server Backend Data Path
1. **Link Capture:** Web UI dashboard receives an online URL string via standard JSON POST request payloads.
2. **URL Validation:** Strict regex and hostname verification restricting to YouTube domains, rejecting shell injection characters.
3. **Stream Stripping:** `yt-dlp` captures the online target isolating raw audio stream channels (`140/bestaudio[ext=m4a]`) while ignoring data-heavy visual tracks.
4. **Media Container Audit:** Inspects media container atoms (`moov/trak/hdlr`) to verify **zero video streams** exist. Rejects and purges any file with video tracks.
5. **Sanitization:** Sanitizes output filenames against FAT32 illegal characters (`/ \ : * ? " < > |`) to prevent MicroSD read errors.

### B. Embedded Playback Pipeline
*   **Storage Access:** SPI communication interface (SCK=14, MISO=16, MOSI=17) with Chip Select driven via `EXIO3` on the onboard `TCA9554` I2C IO expander (`0x20`).
*   **Audio Engine:** Stream blocks pass into dynamically allocated `ESP32-audioI2S` instances.
*   **Signal Output:** Digital audio blocks map onto physical 3-wire I2S lines (`DIN=47`, `LRCK=38`, `BCK=48`), passing into the onboard `PCM5101` DAC with internal PLL to power connected 8Ω micro-speakers.
