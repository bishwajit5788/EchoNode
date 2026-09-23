#include "bluetooth_audio.h"

bool ESP32S3BluetoothAudio::start() {
    Serial.println("[BT] ERROR: Bluetooth A2DP Sink requested, but ESP32-S3 physically lacks Bluetooth Classic (BR/EDR) hardware!");
    Serial.println("[BT] Deterministically rejecting start request (Capability Gated).");
    return false;
}

void ESP32S3BluetoothAudio::stop() {
    // No-op since not supported on ESP32-S3
}
