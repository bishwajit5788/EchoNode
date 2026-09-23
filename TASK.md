# Project Engineering Task Tracking & Execution Plan

- [x] PHASE 1: Web Scraper Backend Architecture Setup
    - [x] Initialize standard Python workspace structure utilizing FastAPI framework rules.
    - [x] Deploy yt-dlp dependencies and configuration scripts.
    - [x] Enforce output filter rules to strip out raw video tracks, saving files purely into audio-only M4A containers.
    - [x] Test the pipeline on local machines using sample YouTube links to verify output audio functionality.

- [x] PHASE 2: Core Hardware Diagnostics & Safety Tuning
    - [x] Perform careful multimeter tests on the battery connector pins to verify alignment with PCB silhouettes (`RULE_POLARITY_CHECK`).
    - [x] Wire up the dual 8Ω micro-speakers via the JST-PH 2.0 headers and run baseline tone check sweeps (`tools/generate_test_tones.py` & `hardware_diagnostics.cpp`).
    - [x] Format target MicroSD cards cleanly to FAT32 formatting constraints using a computer (`tools/sd_card_verifier.py`).

- [x] PHASE 3: Memory-Safe Firmware Synthesis
    - [x] Build baseline initialization code to mount the SPI-driven SD reader board safely.
    - [x] Implement conditional memory structures to switch cleanly between SD and Bluetooth A2DP Sink modes (`RULE_MUTUAL_EXCLUSION`).
    - [x] Program firmware rules to shut down all Wi-Fi/Bluetooth hardware states during local SD file execution.
    - [x] Validate system stability across mode-switches without causing random memory reboots.

- [x] PHASE 4: Visual Interface & Safety Logic Wrap-up
    - [x] Integrate LVGL geometry loops specifically structured for 360x360 round frame screens (`display_manager.cpp`).
    - [x] Program internal clock synchronization hooks during local server file refresh interactions.
    - [x] Build automated safety timer routines that shut down display backlights after defined idle timeouts (`RULE_THERMAL_SHUTDOWN`).
    - [x] Create 3D printable designs or acquire rigid cases to insulate hardware from physical pressure (`enclosure/echonode_bedside_case.scad`).

- [ ] PHASE 5: Deployment, CI/CD & Open-Source Release
    - [ ] Create detailed hardware wiring and pinout documentation (`docs/wiring_guide.md`).
    - [ ] Set up GitHub Actions CI/CD workflows for backend testing and firmware checks.
    - [ ] Add root `Makefile` for developer workflow orchestration.
    - [ ] Initialize Git repository, verify `.gitignore`, and prepare initial release commit.
