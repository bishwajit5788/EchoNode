# EchoNode Firmware - Waveshare ESP32-S3 1.85" Round Display

This directory contains the production firmware for the **EchoNode Bedside Audio Player**, engineered specifically for the **original Waveshare ESP32-S3-Touch-LCD-1.85 Development Board**.

---

## ⚠️ Mandatory Safety Verification Directives

Before connecting any battery or flashing, review and execute these directives:

### 1. `RULE_POLARITY_CHECK` (Hardware First Step)
* Inspect the **MX1.25** LiPo battery connector pins on your battery and the silkscreen markings (`+` / `-`) on the Waveshare PCB.
* **Test with a digital multimeter:** Ensure the positive lead matches `V_BAT` / `+` and negative lead matches `GND` / `-`.
* *Reversed polarity will instantly destroy the onboard lithium battery charging IC.*

### 2. `RULE_VOLUME_CEILING`
* Digital volume is locked in firmware to $\le 65\%$ (`HARD_MAX_VOLUME_LEVEL = 14 / 21`).
* This protects the 8Ω micro-speakers from excessive coil travel and prevents sudden current spikes that trigger battery voltage sags and brownout resets (`TG1WDT_SYS_RESET`).

### 3. `RULE_I2S_MUTING`
* When audio stops or pauses, the I2S bus is zeroed and clocks are muted, cutting off all residual high-frequency idle hiss and electromagnetic interference while you sleep.

### 4. `RULE_THERMAL_SHUTDOWN`
* If audio runs continuously for longer than 30 consecutive minutes without user interaction (`INACTIVITY_TIMEOUT_MS`), the unit triggers deep sleep, cutting off the display backlight on GPIO5 to prevent heat accumulation near bedding.

---

## 🖧 System Architecture & Hardware Truth

* **Target Board:** Original Waveshare ESP32-S3-Touch-LCD-1.85 (ESP32-S3R8, 16MB Flash, 8MB PSRAM OPI).
* **Audio Core:** PCM5101 3-Wire I2S DAC (DIN=47, LRCK=38, BCK=48) with internal PLL.
* **MicroSD Interface:** SPI bus (SCK=14, MISO=16, MOSI=17) with Chip Select routed through **TCA9554 EXIO3** (`0x20` on I2C SDA=11, SCL=10).
* **Display Interface:** 360x360 ST77916 QSPI LCD (DATA0=46, DATA1=45, DATA2=42, DATA3=41, SCK=40, CS=21, BL=5).
* **Flash Partitioning:** 16MB Quad-SPI flash configured with `partitions_16MB.csv` (4MB primary app, 4MB OTA rollout, 2MB LittleFS UI assets, verified via `tools/check_partitions.py`).
* **RAM / PSRAM Strategy:**
  * **Internal SRAM:** Dedicated to real-time I2S DMA ring buffers.
  * **8MB PSRAM (OPI):** Used for LVGL line buffers (`360x40`) and SD file chunk stream caching.
* **Bluetooth Classic Reality:**
  * The ESP32-S3 SoC physically lacks Classic Bluetooth (BR/EDR). Bluetooth A2DP Sink is not supported on bare ESP32-S3.
  * The firmware implements a capability-gated `IBluetoothAudio` interface that reports `NOT_SUPPORTED` on ESP32-S3, keeping wireless radios unpowered during local playback.

---

## 🛠️ Build & Flash Instructions

### Prerequisites
* [PlatformIO Core or VS Code Extension](https://platformio.org/) installed.

### Flashing via PlatformIO
```bash
# Navigate to firmware directory
cd firmware

# 1. Compile and flash main firmware
pio run -e waveshare_esp32s3_round --target upload

# 2. Or flash hardware bench diagnostic self-test
pio run -e diagnostics --target upload

# 3. Open serial monitor (115200 baud)
pio run --target monitor
```

---

## 🎵 Preparing the MicroSD Card

1. Use a MicroSD card $\le 32\text{GB}$.
2. Format the card as **FAT32** using standard allocation unit sizes.
3. Validate your card using `tools/sd_card_verifier.py`.
4. Use the EchoNode Web Scraper backend (`http://localhost:8000`) to extract pure audio-only `.m4a` files directly from YouTube and copy them to the card root directory.
