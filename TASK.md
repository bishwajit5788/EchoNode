# Project Engineering Task Tracking & Execution Plan

### PHASE 1: Web Scraper Backend Architecture Setup
- [x] Initialize standard Python workspace structure utilizing FastAPI framework rules. *(Verified via automated test suite)*
- [x] Deploy yt-dlp dependencies and configuration scripts. *(Verified via automated test suite)*
- [x] Enforce output filter rules to strip out raw video tracks, saving files purely into audio-only M4A containers. *(Verified via test_audio_only.py)*
- [x] Test the pipeline on local machines using sample YouTube links to verify pure audio output functionality. *(Verified via test_extraction_live.py)*

### PHASE 2: Core Hardware Diagnostics & Bench Tooling
- [x] Implement on-board hardware diagnostic self-test suite (`hardware_diagnostics.cpp` & `[env:diagnostics]`). *(Verified in firmware source tree)*
- [x] Implement uncompressed hardware test tone generators for bench frequency sweeps (`tools/generate_test_tones.py`). *(Verified via automated script)*
- [x] Implement MicroSD card FAT32 validator & throughput benchmark tool (`tools/sd_card_verifier.py`). *(Verified via CLI test)*
- [ ] **Physical bench verification:** Perform multimeter tests on battery connector pins against PCB silkscreen (`RULE_POLARITY_CHECK`). *[Physical Bench Pending]*
- [ ] **Physical bench verification:** Wire dual 8Ω micro-speakers via JST-PH 2.0 headers and run on-board tone check sweep. *[Physical Bench Pending]*
- [ ] **Physical bench verification:** Insert physical <=32GB FAT32 MicroSD card and verify on-board mount via TCA9554 EXIO3 CS. *[Physical Bench Pending]*

### PHASE 3: Memory-Safe Firmware Synthesis
- [x] Reconcile authoritative Waveshare ESP32-S3-Touch-LCD-1.85 original pin mapping (LCD, SD, PCM5101, I2C). *(Verified via tools/audit_pin_mappings.py)*
- [x] Eliminate prohibited ESP32-A2DP dependency; implement capability-gated `IBluetoothAudio` interface reporting `NOT_SUPPORTED` on ESP32-S3. *(Verified via CI & audit)*
- [x] Implement real finite state machine (`state_machine.h`) enforcing transition lifecycle: `ACTIVE_A -> mute -> stop -> destroy -> free -> clear pointers -> verify resources -> ACTIVE_B`. *(Verified in audio_manager.cpp)*
- [x] Build TCA9554 IO expander driver controlling MicroSD CS on EXIO3 (`tca9554.cpp` & `sd_manager.cpp`). *(Verified in firmware codebase)*
- [x] Implement deterministic hardware PCM/I2S test path and <=65% volume ceiling enforcement (`RULE_VOLUME_CEILING`). *(Verified in audio_manager.cpp)*
- [ ] **Physical bench verification:** Run continuous start/stop playback cycles on physical ESP32-S3 hardware to record internal heap and PSRAM stability. *[Physical Bench Pending]*

### PHASE 4: Visual Interface & Enclosure Design
- [x] Integrate LVGL 8.3 geometry loops for 360x360 ST77916 circular LCD with PSRAM framebuffers. *(Verified in display_manager.cpp)*
- [x] Implement Screen Alpha (clock, battery, local SD mode, capability-gated BT mode). *(Verified in display_manager.cpp)*
- [x] Implement Screen Beta with strictly 1Hz dynamic updates and volume ceiling indicator. *(Verified in display_manager.cpp)*
- [x] Implement Screen Gamma truthfully explaining Bluetooth Audio is unavailable on ESP32-S3 (no fake A2DP discovery). *(Verified in display_manager.cpp)*
- [x] Implement configurable 30-min idle sleep (`RULE_THERMAL_SHUTDOWN`) and 10s display dimming on GPIO5. *(Verified in power_manager.cpp)*
- [x] Create parametric 3D printable bedside enclosure in OpenSCAD with isolated battery tray and acoustic chambers (`enclosure/echonode_bedside_case.scad`). *(Verified in CAD model)*
- [x] Add high-resolution multi-angle product render, exploded view and visual media structure (`images/README.md`, `images/renders/`, `images/components/`, `images/assembly/`, `images/prototype/`). *(Verified)*

### PHASE 5: Deployment, CI/CD & Open-Source Release
- [x] Create `check_partitions.py` tool verifying 4KB sector alignment, 64KB MMU OTA alignment, and no overlaps. *(Verified against partitions_16MB.csv)*
- [x] Create `audit_pin_mappings.py` verifying exact GPIOs against authoritative Waveshare original board mapping. *(Verified)*
- [x] Update GitHub Actions CI workflow (`.github/workflows/ci.yml`) to run pin audits, partition checks, backend tests, and firmware builds. *(Verified)*
- [x] Synchronize all master documentation files (`PDR.md`, `ARCHITECTURE.md`, `RULES.md`, `DESIGN.md`, `MEMORY.md`, `README.md`, `docs/wiring_guide.md`). *(Verified)*
