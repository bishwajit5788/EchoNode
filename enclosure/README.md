# 🖨️ EchoNode Bedside 3D Printable Enclosure

This directory contains the parametric 3D CAD design for the **EchoNode Bedside Audio Player** enclosure, authored in [OpenSCAD](https://openscad.org/).

---

## 📐 Design Specifications

* **Form Factor:** Low-profile circular bedside puck ($\varnothing 82.0\text{ mm} \times 34.0\text{ mm}$ total height).
* **Display Aperture:** Recessed bezel lip sized for the Waveshare ESP32-S3 1.85-inch Circular Display ($360 \times 360$).
* **Internal Battery Vault:** Isolated compartment dedicated to the **KP Original 702635 600mAh LiPo** ($7.0\text{mm} \times 26.0\text{mm} \times 35.0\text{mm}$) with perimeter air gaps to prevent mechanical compression and heat accumulation near pillows.
* **Dual Acoustic Chambers:** Symmetrical side sound chambers with resonance slits for dual 8Ω micro-speakers connected via JST-PH 2.0 headers.
* **I/O Service Ports:** Recessed cutouts for USB-C (charging & serial) and the MicroSD card push-pull slot.

---

## ⚙️ Recommended Slicer Settings

| Parameter | Recommended Value | Notes |
| :--- | :--- | :--- |
| **Material** | **PETG** (Recommended) or PLA+ | PETG offers superior heat and creep resistance near bedding. |
| **Layer Height** | `0.16 mm` or `0.20 mm` | `0.16 mm` gives smoother circular rim slopes. |
| **Perimeters / Walls** | `3 to 4 walls` | Adds rigidity to protect internal LiPo cell from external weight. |
| **Infill Density** | `25% - 30%` | Gyroid or Honeycomb for balanced acoustic dampening. |
| **Supports** | Minimal / None | Top and bottom shells are oriented flat on the build plate. |

---

## 🛠️ Assembly Instructions

1. **Battery Insertion & Polarity Verification:**
   * Place the KP 702635 battery into the central isolation tray in the bottom shell.
   * **`RULE_POLARITY_CHECK`:** Double-check red (`+`) and black (`-`) wires against the Waveshare PCB silkscreen with a multimeter before connecting the MX1.25 plug.
2. **Speakers:**
   * Slide the two 8Ω micro-speakers into their dedicated left and right acoustic cavities in the bottom shell. Connect to the JST-PH 2.0 headers.
3. **Display & PCB:**
   * Seat the Waveshare 1.85" round display board into the top shell's recessed mounting shelf.
4. **Enclosure Closure:**
   * Align top and bottom shells and fasten using 4x `M2` or `M2.5` $\times 12\text{mm}$ screws through the counter-bored holes on the bottom shell.
