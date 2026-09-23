# EchoNode Firmware - Waveshare ESP32-S3 1.85" Round Display

This directory contains the production firmware for the **EchoNode Bedside Audio Player**, engineered for the Waveshare ESP32-S3 1.85-inch Round Display Development Board.

---

## ⚠️ Mandatory Safety Verification Directives

Before connecting any battery or flashing, review and execute these directives:

### 1. `RULE_POLARITY_CHECK` (Hardware First Step)
* Inspect the **MX1.25** LiPo battery connector pins on your battery and the silk-screen markings (`+` / `-`) on the Waveshare PCB.
* **Test with a digital multimeter:** Ensure the positive lead matches `V_BAT` / `+` and negative lead matches `GND` / `-`.
* *Reversed polarity will instantly destroy the onboard lithium battery charging IC.*

### 2. `RULE_VOLUME_CEILING`
* Digital volume is locked in firmware to $\le 65\%$ (`HARD_MAX_VOLUME_LEVEL = 14 / 21`).
* This protects the 8Ω micro-speakers from excessive coil travel and prevents sudden current spikes that trigger battery voltage sags and ESP32-S3 brownouts.

### 3. `RULE_I2S_MUTING`
* When audio stops or pauses, the I2S bus and external PA amplifier pin (`GPIO 41`) are driven low, cutting off all residual high-frequency idle hiss and electromagnetic interference while you sleep.

### 4. `RULE_THERMAL_SHUTDOWN`
* If audio runs continuously for longer than 30 consecutive minutes without user interaction, the unit triggers deep sleep, cutting off the display backlight to prevent heat accumulation near bedding.

---

## 🖧 System Architecture & Memory Model

* **Flash:** 16MB Quad-SPI flash configured with `partitions_16MB.csv` (4MB App, 2MB LittleFS UI assets, 2x 4.5MB OTA update slots).
* **RAM / PSRAM Strategy:**
  * **Internal SRAM:** Reserved strictly for real-time I2S DMA transmit buffers and Bluetooth A2DP stream packets.
  * **8MB PSRAM (OPI):** Used for LVGL framebuffers (`360x40` line buffers) and SD stream chunk caching.
* **`RULE_MUTUAL_EXCLUSION`:**
  * **SD Local Mode:** Reads audio files (`.m4a`, `.mp3`) from FAT32 MicroSD. Wi-Fi and Bluetooth baseband registers are powered off completely (`WiFi.mode(WIFI_OFF); btStop();`).
  * **Bluetooth Audio Mode:** Acts as an A2DP Sink wireless speaker. MicroSD SPI tasks are safely unmounted.
  * *Both engines never run in RAM concurrently.*

---

## 🛠️ Build & Flash Instructions

### Prerequisites
* [PlatformIO Core or VS Code Extension](https://platformio.org/) installed.

### Flashing via PlatformIO
```bash
# Navigate to firmware directory
cd firmware

# Compile project
pio run

# Upload to Waveshare ESP32-S3 via USB-C
pio run --target upload

# Open serial monitor (115200 baud)
pio run --target monitor
```

---

## 🎵 Preparing the MicroSD Card

1. Use a MicroSD card $\le 32\text{GB}$.
2. Format the card as **FAT32** with standard allocation unit size (e.g. 32KB).
3. Use the EchoNode Web Scraper backend (`http://localhost:8000`) to extract audio-only `.m4a` files directly from YouTube and copy them to the card root directory.
