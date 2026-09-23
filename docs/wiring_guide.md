# 🔌 EchoNode Hardware Wiring & Interconnect Guide

This guide documents the authoritative physical interconnects, pinout mapping, and electrical safety directives for the **original Waveshare ESP32-S3-Touch-LCD-1.85 Development Board**.

---

## ⚠️ Mandatory Safety Verification: `RULE_POLARITY_CHECK`

```
       BATTERY CONNECTOR (MX1.25 2-PIN)
       ┌────────────────────────┐
       │   [ + ]          [ - ] │
       │  RED WIRE      BLACK   │
       │  (V_BAT)       (GND)   │
       └───────────┬────────────┘
                   │
                   ▼  MANDATORY MULTIMETER VERIFICATION
       ┌────────────────────────┐
       │  PCB SILKSCREEN:       │
       │   "+"            "-"   │
       └────────────────────────┘
```

> [!CAUTION]
> **REVERSED BATTERY LEADS DESTROY THE CHARGING IC IMMEDIATELY**:
> Many commercial single-cell LiPo batteries have inverted red/black leads compared to Waveshare's silkscreen markings.
> 1. Set your multimeter to **DC Volts (20V scale)**.
> 2. Touch the RED probe to the battery connector's RED wire contact, and BLACK probe to the BLACK wire.
> 3. Verify a positive voltage reading ($+3.7\text{V}$ to $+4.2\text{V}$).
> 4. Inspect the printed silkscreen markings (`+` and `-`) adjacent to the board's MX1.25 connector.
> 5. Confirm that the positive battery pin aligns with `+` (`V_BAT`) and negative aligns with `-` (`GND`).
> 6. If inverted, lift the plastic retention clips on the MX1.25 plug with fine tweezers to swap the leads before connecting.
> 7. **Bedding Warning:** Never recharge the unit beneath pillows, blankets, or bedding.

---

## 🗺️ Authoritative Pinout Reference Table

### 1. Audio Interconnects (PCM5101 I2S DAC)

| Signal | ESP32-S3 GPIO | Destination | Description |
| :--- | :--- | :--- | :--- |
| **I2S DIN** | `GPIO 47` | PCM5101 DIN | Serial Audio Data Output |
| **I2S LRCK** | `GPIO 38` | PCM5101 LRCK | Word Select (Left/Right Clock) |
| **I2S BCK** | `GPIO 48` | PCM5101 BCK | Bit Clock line |
| **Speaker L/R**| JST-PH 2.0 Headers | Dual 8Ω Micro-Speakers | Connected to onboard speaker amplifier |

*Note: The PCM5101 on this board operates in 3-wire I2S mode with an internal PLL generating SCK from BCK. No external MCLK line is routed or required.*

---

### 2. MicroSD Card (SPI Interface via TCA9554)

| Signal | Routing | Description |
| :--- | :--- | :--- |
| **TF D0 / MISO** | `GPIO 16` | Master In Slave Out |
| **TF CMD / MOSI**| `GPIO 17` | Master Out Slave In |
| **TF SCK** | `GPIO 14` | SPI Clock |
| **TF D3 / CS** | **EXIO3 via TCA9554** | Chip Select (Active LOW via I2C IO expander `0x20`) |

---

### 3. Display Interface (ST77916 QSPI 360x360 Circular LCD)

| Signal | ESP32-S3 GPIO | Description |
| :--- | :--- | :--- |
| **LCD DATA0** | `GPIO 46` | QSPI Data Bit 0 |
| **LCD DATA1** | `GPIO 45` | QSPI Data Bit 1 |
| **LCD DATA2** | `GPIO 42` | QSPI Data Bit 2 |
| **LCD DATA3** | `GPIO 41` | QSPI Data Bit 3 |
| **LCD SCK** | `GPIO 40` | QSPI Clock |
| **LCD CS** | `GPIO 21` | Chip Select |
| **LCD BL** | `GPIO 5` | Backlight PWM control (`ledc` channel 0) |

---

### 4. Shared I2C Bus

| Signal | ESP32-S3 GPIO | Devices on Bus |
| :--- | :--- | :--- |
| **I2C SDA** | `GPIO 11` | CST816S (`0x15`), TCA9554 (`0x20`), PCF8563 (`0x51`) |
| **I2C SCL** | `GPIO 10` | CST816S (`0x15`), TCA9554 (`0x20`), PCF8563 (`0x51`) |

---

### 5. Battery Monitoring ADC

| Signal | ESP32-S3 GPIO | Description |
| :--- | :--- | :--- |
| **BAT_ADC** | `GPIO 1` | Onboard 100k / 100k voltage divider to monitor cell voltage |

---

## 📶 Bluetooth Classic (BR/EDR) Architectural Note

* **Hardware Reality:** The ESP32-S3 SoC only possesses a 2.4GHz Wi-Fi and Bluetooth Low Energy (BLE 5.0) radio. **Classic Bluetooth (BR/EDR) is not present in hardware.**
* **A2DP Audio Sink:** Bluetooth A2DP Sink requires Bluetooth Classic. Therefore, A2DP Sink cannot operate on this board.
* The firmware includes a capability-gated `IBluetoothAudio` interface that deterministically reports `NOT_SUPPORTED` on ESP32-S3, keeping radios powered down.
