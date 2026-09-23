# Product Design Requirements (PDR) - Bedside Audio Device

## 1. Vision & Core Objective
A small, dedicated, hardware-based standalone bedside music player engineered to solve a critical real-world problem: preventing mobile device dependency, cellular thermal radiation, and distracting notification interruptions right before or during sleep.

## 2. Targeted Hardware Environment
*   **Core Controller:** Waveshare ESP32-S3-Touch-LCD-1.85 Development Board (Original Revision).
    *   **Processor:** 32-bit LX7 dual-core running up to 240MHz (ESP32-S3R8).
    *   **Memory Footprint:** 16MB Quad Flash, 8MB Octal PSRAM.
    *   **Display Spec:** 360x360 circular LCD panel (ST77916 QSPI: DATA0=46, DATA1=45, DATA2=42, DATA3=41, SCK=40, CS=21, BL=5).
    *   **Audio Core:** Onboard PCM5101 3-wire I2S DAC (DIN=47, LRCK=38, BCK=48) coupled with onboard speaker amplifier and JST-PH 2.0 miniature speaker pinouts.
*   **Acoustics:** Dual 8Ω micro-speakers connected directly via JST-PH 2.0 cables.
*   **Power System:** KP Original 702635 600mAh 3.7V single-cell rechargeable Lithium-Polymer (LiPo) battery.
*   **Storage Expansion:** MicroSD Card slot (FAT32, restricted to <= 32GB; SPI interface: MISO=16, MOSI=17, SCK=14, CS=TCA9554 EXIO3).
*   **IO Expander & Peripherals:** TCA9554 at I2C `0x20` (SDA=11, SCL=10), CST816S touch controller at `0x15`, PCF8563 RTC at `0x51`.

## 3. Web Service Specifications
*   **Functionality:** A minimalist web service interface capable of taking a user-submitted YouTube URL link.
*   **Extraction Engine:** Automated extraction of video containers down to video-free audio-only streams wrapped inside `.m4a` or `.mp3` files.
*   **Container Validation:** Strict rejection of any container holding a video stream track.
*   **Fulfillment Pipeline:** Transfer mechanism targeting storage expansion via physical SD Card swapping, USB-C Mass Storage drive emulation, or local home Wi-Fi network POST synchronization loops.

## 4. Operational Boundaries & Constraints
*   **Zero Notification Environment:** The system must enforce absolute isolation from cellular push payloads during sleep cycles.
*   **Bluetooth Classic Reality:** The ESP32-S3 SoC physically lacks Classic Bluetooth (BR/EDR). Bluetooth A2DP Sink is not supported on bare ESP32-S3; radios remain powered off during local playback.
*   **Thermal Safety:** Strict limits preventing operational heat entrapment when the device sits near bedding arrays or pillows. A 30-minute idle sleep timeout cuts off backlights. Recharging beneath pillows or bedding is strictly prohibited.
*   **Battery Power Sag:** Safe management of current demands enforcing a hard volume ceiling <= 65% to prevent internal system rails from sagging and tripping brownout loops.
