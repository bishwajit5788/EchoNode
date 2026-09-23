# Product Design Requirements (PDR) - Bedside Audio Device

## 1. Vision & Core Objective
A small, dedicated, hardware-based standalone bedside music player engineered to solve a critical real-world problem: preventing mobile device dependency, cellular thermal radiation, and distracting notification interruptions right before or during sleep.

## 2. Targeted Hardware Environment
*   **Core Controller:** Waveshare ESP32-S3 1.85-inch Round Display Development Board.
    *   **Processor:** 32-bit LX7 dual-core running up to 240MHz.
    *   **Memory Footprint:** 16MB Flash, 8MB PSRAM.
    *   **Display Spec:** 360x360 circular LCD panel.
    *   **Audio Core:** Onboard I2S audio decoding chip (ES8311/PCM5101 equivalent) coupled with miniature speaker pinout headers.
*   **Acoustics:** Dual 8Ω micro-speakers connected directly via JST-PH 2.0 cables.
*   **Power System:** KP Original 702635 600mAh 3.7V single-cell rechargeable Lithium-Polymer (LiPo) battery.
*   **Storage Expansion:** MicroSD Card slot (FAT32, restricted to <= 32GB memory size).

## 3. Web Service Specifications
*   **Functionality:** A minimalist web service interface capable of taking a user-submitted YouTube URL link.
*   **Extraction Engine:** Automated extraction of video containers down to video-free audio-only streams wrapped inside `.mp4` or `.m4a` files.
*   **Fulfillment Pipeline:** Transfer mechanism targeting storage expansion via physical SD Card swapping, USB-C Mass Storage drive emulation, or local home Wi-Fi network POST synchronization loops.

## 4. Operational Boundaries & Constraints
*   **Zero Notification Environment:** The system must enforce absolute isolation from cellular push payloads during sleep cycles.
*   **Thermal Safety:** Strict limits preventing operational heat entrapment when the device sits near bedding arrays or pillows.
*   **Battery Power Sag:** Safe management of current demands to prevent internal system rails from sagging and tripping brownout loops.
