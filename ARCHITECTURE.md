# System Architecture & Technical Topology

## 1. Dual Operational Profile Matrix

```
┌──────────────────────────────────┐
│    ESP32-S3 Firmware System     │
└────────────────┬─────────────────┘
                 │
┌────────────────┴───────────────────────┐
▼                                       ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     Standalone SD Mode        │       │     Bluetooth Audio Mode      │
├───────────────────────────────┤       ├───────────────────────────────┤
│ • Wi-Fi / Bluetooth: OFF      │       │ • Wi-Fi: OFF                  │
│ • Reads MP4/MP3 from SD card  │       │ • Bluetooth A2DP: SINK Active │
│ • Zero phone notifications    │       │ • Acts as a wireless speaker  │
│ • Maximum battery savings     │       │ • Phone handles notifications │
└───────────────────────────────┘       └───────────────────────────────┘
```

## 2. Subsystem Breakdowns

### A. Web Server Backend Data Path
1. **Link Capture:** Web UI dashboard receives an online URL string via standard JSON POST request payloads.
2. **Stream Stripping:** `yt-dlp` captures the online target and isolates the raw audio stream channel while ignoring data-heavy visual tracks.
3. **Containerization:** The output stream is enclosed in a video-free audio-only M4A/MP4 structure (codec tracking matching AAC/MP3 specifications) to minimize computing demands during runtime decoding.

### B. Embedded Playback Pipeline
*   **Storage Access:** SPI communication interface reading chunks from the onboard MicroSD connector slot.
*   **Audio Engine:** Stream blocks pass into the `ESP32-audioI2S` structural pipeline.
*   **Signal Output:** Digital audio blocks map cleanly onto physical I2S lines (`BCLK`, `LRCK`, `DOUT`), passing safely into the onboard decoder array to directly power the connected 8Ω micro-speakers.

### C. Wireless Streaming Sink
*   **Protocol Core:** Bluetooth A2DP Sink configuration via `ESP32-A2DP`.
*   **Execution Profile:** The board appears as an audio peripheral to a paired mobile smartphone, routing real-time audio streams straight down the shared physical I2S pin layout.
