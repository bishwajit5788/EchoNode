# Operational Safety, Firmware Policies & Constraints

## 1. Electrical & Thermal Safety Directives
*   **RULE_POLARITY_CHECK:** Before initial battery contact, the polarization vectors of the MX1.25 connector must be visually verified against the physical silkscreen marking on the development PCB. Swapped positive/negative leads will destroy the charging integrated circuit.
*   **RULE_THERMAL_SHUTDOWN:** If internal audio loops run continuously for longer than 30 consecutive minutes without user input, the system must invoke an automatic sleep timeout, cutting off display backlights to eliminate risk of heat entrapment near bedding.
*   **RULE_CHARGING_SAFETY:** Never initiate cell recharging while the physical unit is positioned directly beneath or against pillows or blankets. 

## 2. Firmware Compilation & Resource Policies
*   **RULE_MUTUAL_EXCLUSION:** Memory spaces dedicated to the SD audio track decoder and the Bluetooth A2DP software stack must never coexist in RAM active allocations simultaneously. Switching profiles requires explicit teardown and de-allocation calls before establishing a new profile.
*   **RULE_VOLUME_CEILING:** Digital volume mapping configurations must be hard-capped at an upper boundary of 60% to 70%. This prevents dynamic speaker coil distortion and guards against sudden voltage sags that can cause brownout loop crashes.
*   **RULE_I2S_MUTING:** When playback is paused or the queue is fully cleared, the software must trigger code-level mute sequences on the I2S bus. This removes electromagnetic interference and eliminates residual high-frequency idle hiss.
