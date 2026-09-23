# Operational Safety, Firmware Policies & Constraints

## 1. Electrical & Thermal Safety Directives
*   **RULE_POLARITY_CHECK:** Before initial battery contact, the polarization vectors of the MX1.25 connector must be verified with a digital multimeter against the physical silkscreen marking on the Waveshare PCB. Swapped positive/negative leads will destroy the onboard charging integrated circuit.
*   **RULE_THERMAL_SHUTDOWN:** If internal audio loops run continuously for longer than 30 consecutive minutes without user input (`INACTIVITY_TIMEOUT_MS`), the system must invoke an automatic sleep timeout, cutting off display backlights on GPIO5 to eliminate risk of heat entrapment near bedding.
*   **RULE_CHARGING_SAFETY:** Never initiate cell recharging while the physical unit is positioned directly beneath or against pillows, blankets, or bedding. 

## 2. Firmware Compilation & Resource Policies
*   **RULE_MUTUAL_EXCLUSION:** Memory spaces dedicated to the SD audio track decoder and any wireless audio software stack must never coexist in RAM active allocations simultaneously. Transitioning between profiles requires explicit teardown, decoder destruction, buffer freeing, pointer clearing, and memory verification before establishing a new profile.
*   **RULE_VOLUME_CEILING:** Digital volume mapping configurations must be hard-capped at an upper boundary of <= 65% (`HARD_MAX_VOLUME_LEVEL = 14 / 21`). This prevents dynamic speaker coil distortion and guards against sudden voltage sags that trip brownout loop crashes.
*   **RULE_I2S_MUTING:** When playback is paused or the queue is fully cleared, the software must trigger code-level mute sequences on the I2S bus, clear DMA buffers, and disable active clocking to eliminate electromagnetic interference and residual high-frequency idle hiss.
*   **RULE_STORAGE_BOUNDARY:** MicroSD storage cards must strictly comply with FAT32 formatting and a capacity ceiling of <= 32GB to avoid unhandled exFAT cluster structures on the SPI bus.
