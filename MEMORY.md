# Memory Allocation & Hardware Partition Layout

## 1. Storage Flash Layout Structure (16MB Onboard Flash)

```
┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│  Bootloader + App Space │     SPIFFS/LittleFS     │     OTA Update Slots    │
│        (4.0 MB)         │  (2.0 MB - UI Assets)   │   (2x 4.5 MB Rollouts)  │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

## 2. Internal RAM & PSRAM Management Rules

### A. Local Storage File Playback Profile
*   **DMA Audio Channel Buffers:** Allocates critical tracking space inside fast internal SRAM to feed real-time I2S data streams seamlessly without stalling.
*   **SPI SD Card Input Stream Array:** Allocates data stream arrays into external 8MB PSRAM regions to hold large chunks of incoming audio data, preventing buffer runouts.
*   **Radio Transceiver Overhead:** Wireless transceivers are forced completely offline. Wi-Fi and Bluetooth memory allocations are completely cleared, maximizing available system workspace.

### B. Wireless Bluetooth Sync Mode Profile
*   **Bluetooth Stack Allocation:** The A2DP Sink controller assumes primary control over internal SRAM allocations to process real-time incoming wireless frames without frame loss.
*   **Storage Access Lock:** The MicroSD storage system file system tasks are unmounted and put into low-power states to prevent bus traffic collisions on shared SPI lines.
*   **Audio Decompression Cache:** Decoded real-time PCM wireless frame arrays are allocated into external PSRAM structures before passing straight down to the physical audio output channels.
