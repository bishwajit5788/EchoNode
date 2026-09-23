# 📸 EchoNode Image & Media Documentation

This directory houses all visual documentation, design renders, component photos, and assembly build logs for the **EchoNode Bedside Audio Player** project.

---

## 📁 Directory Structure

```
images/
├── README.md               # Visual asset guidelines and hardware photo staging
├── renders/                # High-resolution 3D CAD renders and infographics
│   └── EchoNode-multi-angle.jpg  # Multi-angle product render, exploded view & dimensions
├── components/             # Unboxing & bench photos of bare hardware modules
│   └── .gitkeep            # Staging for received components (Waveshare LCD, PCM5101, speakers, LiPo)
├── assembly/               # Step-by-step physical assembly & wiring photos
│   └── .gitkeep            # Staging for soldering, harness routing, and enclosure fitting
└── prototype/              # Bench testing, oscilloscope/multimeter verification, and live demos
    └── .gitkeep            # Staging for diagnostic screen, sleep test, and battery measurement
```

---

## 🖼️ Active Visual Assets

### 1. `renders/EchoNode-multi-angle.jpg`
* **Resolution:** 1024 × 682 (Standard 3:2 JFIF baseline JPEG)
* **SHA-256:** `88f4ac985d4829291b5230c04ee474b6b42d16b2e5aad39184ccdff016021594`
* **Contents:**
  - **Front View (Angled & Straight):** 360×360 ST77916 circular display running Screen Beta (album art, track time, volume ceiling indicator).
  - **Side Views (Left & Right):** Low-profile knurled control ring and CNC machined bevels.
  - **Back View:** Perforated acoustic speaker grille with 8Ω driver venting.
  - **Exploded View:** Front glass, circular LCD module, structural frame, main ESP32-S3R8 PCB, PCM5101 DAC board, 600mAh LiPo battery (702635), and rear case.
  - **Internal Top View:** Authoritative Waveshare board layout showing ESP32-S3R8 (16MB Flash, 8MB PSRAM), MicroSD slot, TCA9554 IO expander (EXIO3 CS), PCM5101 DAC I2S interface, and LiPo battery header.
  - **Dimensions:** 60 mm diameter × 20 mm thickness.
  - **Lifestyle Context:** Bedside table placement demonstrating zero phone distraction.

---

## 🛠️ Hardware Procurement & Photo Checklist

When physical components are received, add photos according to the following conventions:

### `components/` (Hardware Sourcing)
* `esp32s3_waveshare_front.jpg` — Original Waveshare ESP32-S3-Touch-LCD-1.85 front with circular LCD.
* `esp32s3_waveshare_back.jpg` — PCB backside showing silkscreen, TCA9554, and JST headers.
* `pcm5101_dac_board.jpg` — Audio DAC board showing 3-wire I2S pins (DIN=47, LRCK=38, BCK=48).
* `speakers_8ohm.jpg` — Dual 8Ω miniature acoustic drivers with JST-PH 2.0 connectors.
* `lipo_battery_polarity.jpg` — KP 702635 600mAh battery showing multimeter polarity check (`RULE_POLARITY_CHECK`).
* `enclosure_3d_print.jpg` — 3D printed bedside case parts (`echonode_bedside_case.scad`).

### `assembly/` (Build Progression)
* `01_polarity_verification.jpg` — Multimeter verifying battery connector polarity against silkscreen.
* `02_speaker_wiring.jpg` — Speaker wires terminated to JST-PH 2.0 headers.
* `03_board_stack_install.jpg` — Securing PCB and DAC inside lower enclosure shell.
* `04_battery_placement.jpg` — Battery seated in isolated tray away from heat-generating components.
* `05_final_closure.jpg` — Snapping enclosure lid and checking button/port clearances.

### `prototype/` (Bench Verification)
* `bench_diagnostics_screen.jpg` — Unit running `[env:diagnostics]` with hardware self-test pass.
* `bench_playback_screen.jpg` — Unit playing 440Hz sine test tone or local SD track.
* `current_draw_sleep.jpg` — Multimeter / Nordic Power Profiler showing deep sleep current consumption.
