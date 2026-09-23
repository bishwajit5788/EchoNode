# Graphical Interface Design & Display Architecture

## 1. Frame Buffer Coordinates & Visual Form Factors
*   **Display Geometry:** Perfect 1:1 circular screen layout.
*   **Pixel Matrix:** 360x360 resolution frame limits on ST77916 QSPI display.
*   **Backlight Control:** PWM controlled via `GPIO 5`.
*   **Graphics Engine:** UI construction utilizing the LVGL 8.3 framework with PSRAM framebuffers to protect internal SRAM for audio DMA.

## 2. Interactive Page Layouts

### Screen Alpha: Boot / Standby Dashboard
*   **Central Asset:** Large digital time readout refreshed cleanly from the internal Real-Time Clock (RTC).
*   **Status Bars:** A battery fuel gauge tracking voltage changes via ADC (GPIO1) and displaying a low power visual warning when cells descend to 3.5V.
*   **Control Mechanisms:** Two distinct profile selector buttons:
    *   Button Left: [Standalone SD Local Profile] - Enters local SD playback.
    *   Button Right: [Bluetooth Audio (Gated)] - Leads to Screen Gamma status display.

### Screen Beta: Standalone Local Playback Interface
*   **Static Rendering:** Audio metadata tracking lines and layout frames remain strictly static to reduce SPI bus congestion.
*   **Dynamic Truncation:** Playback time status text digits update exactly once per second (1Hz), minimizing display refreshes to avoid introducing line audio crackle.
*   **Volume Ceiling Indicator:** Explicitly displays current volume and indicates the hard safety cap of 65%.
*   **Control Matrix:** Minimalist navigation buttons (Play/Pause/Next/Prev/Return-To-Menu). The panel backlight shuts off completely after 10 seconds of user interaction idle timeouts (`DISPLAY_IDLE_TIMEOUT_MS`).

### Screen Gamma: Bluetooth Hardware Capability Status
*   **Truthful Hardware Status:** Does NOT fake an active A2DP discovery sequence.
*   **Notice Field:** Displays "Bluetooth Audio Unavailable" informing the user that the ESP32-S3 SoC physically lacks Classic Bluetooth (BR/EDR) hardware.
*   **Return Interface:** A high-visibility tactile boundary escape button to jump safely back to Standby.
