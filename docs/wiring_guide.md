# 🔌 EchoNode Hardware Wiring & Interconnect Guide

This guide provides the complete physical wiring, pinout mapping, and electrical safety directives for assembling the **EchoNode** bedside music player using the **Waveshare ESP32-S3 1.85-inch Round Display Development Board**.

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
                   ▼  VERIFY WITH MULTIMETER FIRST!
       ┌────────────────────────┐
       │  PCB SILKSCREEN:       │
       │   "+"            "-"   │
       └────────────────────────┘
```

> [!CAUTION]
> **REVERSED BATTERY LEADS WILL DESTROY THE CHARGING IC IMMEDIATELY**:
> Many off-the-shelf single-cell LiPo batteries with pre-crimped MX1.25 connectors have inverted red/black leads compared to development board silkscreens.
> 1. Set your digital multimeter to **DC Volts (20V range)**.
> 2. Touch the RED multimeter probe to the battery connector's RED wire contact, and BLACK probe to the BLACK wire.
> 3. Verify the reading is positive ($+3.7\text{V}$ to $+4.2\text{V}$).
> 4. Inspect the silkscreen printed on the Waveshare PCB adjacent to the MX1.25 socket.
> 5. Confirm that the positive pin aligns with `+` / `V_BAT` and the negative pin aligns with `-` / `GND`.
> 6. If inverted, use a fine needle or precision tweezers to lift the plastic retention tab on the MX1.25 plug and swap the pin positions before plugging it in.

---

## 🗺️ Pinout Reference Table

### 1. Audio Interconnects (I2S & Power Amplifier)

| Function | ESP32-S3 GPIO | Destination | Description |
| :--- | :--- | :--- | :--- |
| **I2S BCLK** | `GPIO 39` | ES8311 / DAC BCLK | Bit Clock line |
| **I2S LRCK / WS**| `GPIO 38` | ES8311 / DAC LRCK | Word Select / Left-Right Clock |
| **I2S DOUT** | `GPIO 40` | ES8311 / DAC DIN | Serial Audio Data Output |
| **I2S MCLK** | `GPIO 2` | ES8311 MCLK | Master Clock (required by ES8311) |
| **PA Enable** | `GPIO 41` | Audio Amp SHDN/EN | Hardware Mute (Active HIGH, pulled LOW during mute) |
| **Speaker L/R**| JST-PH 2.0 Headers | Dual 8Ω Micro-Speakers | Connected directly to onboard amplifier output headers |

---

### 2. MicroSD Card SPI Interface

| Signal | ESP32-S3 GPIO | Description |
| :--- | :--- | :--- |
| **SD CS** | `GPIO 14` | Chip Select (Active LOW) |
| **SD SCK** | `GPIO 15` | SPI Clock (Up to 20MHz sustained) |
| **SD MOSI** | `GPIO 16` | Master Out Slave In |
| **SD MISO** | `GPIO 17` | Master In Slave Out |

---

### 3. Display & Touch Controller

| Signal | ESP32-S3 GPIO | Description |
| :--- | :--- | :--- |
| **LCD BL** | `GPIO 6` | Backlight PWM control (`ledc` channel 0) |
| **Touch SDA** | `GPIO 4` | I2C Data (CST816S capacitive touch) |
| **Touch SCL** | `GPIO 5` | I2C Clock (CST816S capacitive touch) |
| **Touch INT** | `GPIO 7` | Touch interrupt (active LOW, used for deep sleep wake) |
| **Touch RST** | `GPIO 13` | Touch controller hardware reset |

---

### 4. Battery Monitoring ADC

| Signal | ESP32-S3 GPIO | Circuit Details |
| :--- | :--- | :--- |
| **BAT_ADC** | `GPIO 1` | Connected to internal 1:1 voltage divider ($100\text{k}\Omega / 100\text{k}\Omega$). Full charge $4.2\text{V} \rightarrow 2.1\text{V}$ on pin. |

---

## 🔊 Acoustics & Speaker Wiring

* **Acoustics Spec:** Two miniature 8Ω micro-speakers ($\sim 1.0\text{W}\text{--}1.5\text{W}$, dimensions $15\text{mm} \times 24\text{mm}$ or $20\text{mm}$ round).
* **Connection:** Crimp into 2-pin JST-PH 2.0mm female housing connectors and plug directly into the board's speaker headers.
* **Phase Alignment:** Ensure both speakers share identical polarity wiring (Pin 1 to `+`, Pin 2 to `-`) so low-frequency acoustic waves constructively reinforce rather than cancel out inside the enclosure cavities.
* **Distortion Prevention (`RULE_VOLUME_CEILING`):** Firmware restricts maximum volume to $65\%$ ($14/21$ steps), preventing thermal coil overload and sudden current draw spikes that cause brownout resets (`TG1WDT_SYS_RESET`).
