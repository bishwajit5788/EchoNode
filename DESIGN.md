# Graphical Interface Design & Display Architecture

## 1. Frame Buffer Coordinates & Visual Form Factors
*   **Display Geometry:** Perfect 1:1 circular screen layout.
*   **Pixel Matrix:** 360x360 resolution frame limits.
*   **Graphics Engine:** UI construction utilizing the LVGL framework.

## 2. Interactive Page Layout Layouts

### Screen Alpha: Boot / Standby Dashboard
*   **Central Asset:** Large digital time readout refreshed cleanly from the internal Real-Time Clock (RTC).
*   **Status Bars:** A battery fuel gauge tracking voltage changes and displaying a low power visual warning when cells descend to 3.5V.
*   **Control Mechanisms:** Two distinct, large touch-sensitive profile selector button icons:
    *   Button Left: [Standalone SD Local Profile]
    *   Button Right: [Bluetooth Audio Receiver Mode]

### Screen Beta: Standalone Local Playback Interface
*   **Static Rendering:** Audio metadata tracking lines and layout frames remain strictly static to reduce SPI bus congestion.
*   **Dynamic Truncation:** Playback time status text digits update exactly once per second, minimizing display refreshes to avoid introducing line audio crackle.
*   **Control Matrix:** Minimalist navigation buttons (Play/Pause/Return-To-Menu). The panel backlight shuts off completely after 10 seconds of user interaction idle timeouts.

### Screen Gamma: Wireless Bluetooth Sync Monitor
*   **Visual Elements:** Pulsing connection discovery animation sequence.
*   **Display Fields:** Connected mobile phone name field readout.
*   **Return Interface:** A simple, high-visibility tactile boundary escape button to quickly close Bluetooth operations and jump safely back to Standby.
