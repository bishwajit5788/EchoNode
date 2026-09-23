# Memory Allocation & Hardware Partition Layout

## 1. Storage Flash Layout Structure (16MB Onboard Flash)

Validated via `tools/check_partitions.py` against `firmware/partitions_16MB.csv`:

```
0x000000 ┌──────────────────────────────────────────────┐
         │ Bootloader (32 KB) + Partition Table (4 KB)  │
0x009000 ├──────────────────────────────────────────────┤
         │ NVS (20 KB)                                  │
0x00E000 ├──────────────────────────────────────────────┤
         │ OTA Data (8 KB)                              │
0x010000 ├──────────────────────────────────────────────┤
         │ app0 (ota_0) - Primary Firmware (4.00 MB)    │
0x410000 ├──────────────────────────────────────────────┤
         │ app1 (ota_1) - Secondary Rollout (4.00 MB)   │
0x810000 ├──────────────────────────────────────────────┤
         │ SPIFFS / LittleFS - UI Assets (2.00 MB)      │
0xA10000 ├──────────────────────────────────────────────┤
         │ Unallocated Headroom / Expansion (5.94 MB)   │
0x1000000└──────────────────────────────────────────────┘
```

* **4KB Alignment:** All partition offsets and sizes are strictly aligned to 4096-byte boundaries.
* **64KB MMU Alignment:** Both `app0` (`0x10000`) and `app1` (`0x410000`) adhere to ESP32-S3 64KB MMU flash page boundaries.

---

## 2. Internal RAM & PSRAM Management Rules

### A. Local Storage File Playback Profile
*   **DMA Audio Channel Buffers:** Allocates real-time I2S transmit ring buffers inside fast internal SRAM to feed PCM5101 I2S clocks (`DIN=47`, `LRCK=38`, `BCK=48`) seamlessly without underruns.
*   **Audio File Stream Buffers:** Allocates incoming stream chunks and metadata structures into external 8MB PSRAM regions to conserve internal SRAM.
*   **LVGL Frame Buffers:** Allocates 360x40 line draw buffers in external PSRAM (`ps_malloc`) to avoid starving internal heap.
*   **Radio Transceiver Overhead:** Wireless transceivers are forced completely offline (`WiFi.mode(WIFI_OFF)`). Wi-Fi and Bluetooth baseband registers are unpowered.
*   **Leak Accounting:** Pre- and post-allocation memory snapshots are recorded upon every state transition to ensure zero memory leaks during repeated start/stop cycles.

### B. Mutual Exclusion & Lifecycle Protection
*   The decoder instance is created dynamically only when transitioning to `LOCAL_SD_ACTIVE`.
*   Upon stopping or entering standby, the decoder instance is explicitly stopped, deleted, its pointers set to `nullptr`, and SD storage unmounted.
