#include <Arduino.h>
#include "config.h"
#include "power_manager.h"
#include "sd_manager.h"
#include "audio_manager.h"
#include "display_manager.h"

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n==================================================");
    Serial.println("   EchoNode - Bedside Audio Device Initializing   ");
    Serial.println("   Hardware: Waveshare ESP32-S3 1.85\" Round LCD   ");
    Serial.println("==================================================");

    // 1. Initialize Power and Battery Management
    Serial.println("[INIT] Step 1: Power & Backlight Manager...");
    PowerManager::instance().begin();

    // 2. Initialize Audio Hardware & Safety Directives
    Serial.println("[INIT] Step 2: Audio Engine (RULE_VOLUME_CEILING & I2S Muting)...");
    AudioManager::instance().begin();

    // 3. Initialize LVGL 360x360 Round Display
    Serial.println("[INIT] Step 3: Round UI (LVGL Screens Alpha, Beta, Gamma)...");
    DisplayManager::instance().begin();

    Serial.println("[INIT] EchoNode ready in STANDBY mode.");
}

void loop() {
    // 1. Feed real-time audio chunk decoding loop
    AudioManager::instance().loop();

    // 2. Handle LVGL rendering and input loops
    DisplayManager::instance().loop();

    // 3. Monitor sleep timeouts, 10s backlight dimming, and 30m thermal safety
    PowerManager::instance().update();

    // 4. Yield time to FreeRTOS idle task
    vTaskDelay(pdMS_TO_TICKS(5));
}
