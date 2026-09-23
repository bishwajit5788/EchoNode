# Contributing to EchoNode 🌙

We welcome open-source contributions to **EchoNode**! Whether you are improving the embedded firmware, optimizing the web audio extraction engine, or enhancing the 3D printable enclosure, we appreciate your help.

---

## 📜 Development Guidelines

### 1. Mandatory Safety & Architecture Directives
All pull requests must strictly comply with the core rules defined in [RULES.md](RULES.md) and [MEMORY.md](MEMORY.md):
* **`RULE_MUTUAL_EXCLUSION`:** Audio SD playback (`ESP32-audioI2S`) and Bluetooth A2DP Sink (`ESP32-A2DP`) memory stacks must NEVER coexist in active RAM allocations.
* **`RULE_VOLUME_CEILING`:** Never increase digital volume ceiling past $65\%$ ($14/21$ steps).
* **`RULE_I2S_MUTING`:** Always mute the external power amplifier and drive zero-frames during pause/stop transitions.
* **`RULE_THERMAL_SHUTDOWN`:** Preserve the 30-minute idle sleep timeout for bedding safety.

### 2. Code Style
* **Python Backend:** Formatted with `black` / `ruff`, type hints on all route functions and Pydantic models.
* **C++ Firmware:** Formatted with Google / LLVM C++ standard. PSRAM allocations using `ps_malloc()` for large buffers.
* **OpenSCAD:** Parametric dimensions with clear variable names.

---

## 🛠️ Submitting Changes

1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Verify local tests pass:
   ```bash
   make test-backend
   ```
3. Commit your changes with concise, descriptive commit messages:
   ```bash
   git commit -am "Add feature X"
   ```
4. Push to your branch and open a Pull Request.

---

## 📄 License
By contributing to EchoNode, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
