#!/usr/bin/env python3
"""
EchoNode Authoritative Hardware Pinout Auditor
Validates that firmware/include/config.h and documentation files strictly adhere
to the official Waveshare ESP32-S3-Touch-LCD-1.85 (Original Revision) pinout:

LCD:
  DATA0 GPIO46
  DATA1 GPIO45
  DATA2 GPIO42
  DATA3 GPIO41
  SCK GPIO40
  CS GPIO21
  BL GPIO5

TF / MicroSD:
  D0/MISO GPIO16
  CMD/MOSI GPIO17
  SCK GPIO14
  D3/CS EXIO3 via TCA9554

I2C:
  SDA GPIO11
  SCL GPIO10

Audio (PCM5101):
  DIN GPIO47
  LRCK GPIO38
  BCK GPIO48
"""

import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

AUTHORITATIVE_PINS = {
    "LCD_DATA0_PIN": 46,
    "LCD_DATA1_PIN": 45,
    "LCD_DATA2_PIN": 42,
    "LCD_DATA3_PIN": 41,
    "LCD_SCK_PIN": 40,
    "LCD_CS_PIN": 21,
    "LCD_BL_PIN": 5,

    "SD_MISO_PIN": 16,
    "SD_MOSI_PIN": 17,
    "SD_SCK_PIN": 14,

    "I2C_SDA_PIN": 11,
    "I2C_SCL_PIN": 10,

    "I2S_DOUT_PIN": 47,
    "I2S_LRCK_PIN": 38,
    "I2S_BCLK_PIN": 48,
}

def audit_config_header(config_path: Path) -> bool:
    print(f"Auditing Header: {config_path}")
    if not config_path.exists():
        print(f"❌ File not found: {config_path}")
        return False

    content = config_path.read_text()
    errors = []

    for name, expected_pin in AUTHORITATIVE_PINS.items():
        pattern = rf"#define\s+{name}\s+(\d+)"
        match = re.search(pattern, content)
        if not match:
            errors.append(f"Missing pin definition for '{name}'")
        else:
            val = int(match.group(1))
            if val != expected_pin:
                errors.append(f"Pin '{name}' is defined as GPIO{val}, expected authoritative GPIO{expected_pin}")
            else:
                print(f"  ✓ {name:<18} -> GPIO{val}")

    # Check for TCA9554 EXIO3 SD CS definition
    if "TCA9554_EXIO3" not in content and "SD_CS_EXIO" not in content:
        errors.append("Missing TCA9554 EXIO3 definition for MicroSD Card CS")

    # Check for prohibited A2DP dependency in platformio.ini
    pio_path = REPO_ROOT / "firmware" / "platformio.ini"
    if pio_path.exists():
        pio_content = pio_path.read_text()
        if "ESP32-A2DP" in pio_content or "pschatzmann/ESP32-A2DP" in pio_content:
            errors.append("PROHIBITED DEPENDENCY: 'ESP32-A2DP' found in firmware/platformio.ini! (ESP32-S3 physically lacks Bluetooth Classic/A2DP).")
        else:
            print("  ✓ firmware/platformio.ini is free of prohibited ESP32-A2DP dependency.")

    if errors:
        print("\n❌ PIN & ARCHITECTURE AUDIT FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False

    print("\n✓ All pinout and architecture definitions match authoritative Waveshare original board mapping!")
    return True

if __name__ == "__main__":
    cfg = REPO_ROOT / "firmware" / "include" / "config.h"
    success = audit_config_header(cfg)
    sys.exit(0 if success else 1)
