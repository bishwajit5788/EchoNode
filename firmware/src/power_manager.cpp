#include "power_manager.h"
#include <esp_sleep.h>

#define PWM_CHANNEL 0
#define PWM_FREQ    5000
#define PWM_RES     8

PowerManager::PowerManager()
    : m_lastActivityMs(0),
      m_audioPlaybackStartMs(0),
      m_backlightAwake(true),
      m_currentBrightness(200) {}

void PowerManager::begin() {
    // Configure Backlight PWM via LEDC on GPIO5 (Authoritative original board mapping)
    ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RES);
    ledcAttachPin(LCD_BL_PIN, PWM_CHANNEL);
    setBacklightBrightness(200);

    // ADC setup for battery gauge on GPIO1
    analogReadResolution(12); // 0-4095
    analogSetAttenuation(ADC_11db); // Up to ~3.1V

    m_lastActivityMs = millis();
    m_audioPlaybackStartMs = millis();
}

void PowerManager::noteUserActivity() {
    m_lastActivityMs = millis();
    if (!m_backlightAwake) {
        setBacklightBrightness(200);
        m_backlightAwake = true;
    }
}

float PowerManager::getBatteryVoltage() {
    uint32_t raw = analogRead(BATTERY_ADC_PIN);
    // Convert 12-bit ADC reading to voltage using reference and 100k/100k divider
    float pinVoltage = (raw / 4095.0f) * 3.3f;
    return pinVoltage * BATTERY_ADC_DIVIDER;
}

int PowerManager::getBatteryPercentage() {
    float voltage = getBatteryVoltage();
    if (voltage >= BATTERY_FULL_V) return 100;
    if (voltage <= BATTERY_MIN_SAFE_V) return 0;
    return (int)(((voltage - BATTERY_MIN_SAFE_V) / (BATTERY_FULL_V - BATTERY_MIN_SAFE_V)) * 100.0f);
}

bool PowerManager::isBatteryLow() {
    return getBatteryVoltage() < BATTERY_MIN_SAFE_V;
}

void PowerManager::setBacklightBrightness(uint8_t brightness) {
    m_currentBrightness = brightness;
    if (brightness == 0) {
        ledcWrite(PWM_CHANNEL, 0);
        pinMode(LCD_BL_PIN, OUTPUT);
        digitalWrite(LCD_BL_PIN, LOW); // Explicit hard-pull low on GPIO5
        m_backlightAwake = false;
    } else {
        ledcAttachPin(LCD_BL_PIN, PWM_CHANNEL);
        ledcWrite(PWM_CHANNEL, brightness);
        m_backlightAwake = true;
    }
}

void PowerManager::update() {
    unsigned long now = millis();

    // RULE_THERMAL_SHUTDOWN: 30 minutes continuous without touch interaction
    if (now - m_lastActivityMs > INACTIVITY_TIMEOUT_MS) {
        Serial.println("[SAFETY] RULE_THERMAL_SHUTDOWN triggered! 30m idle elapsed near bedding.");
        enterDeepSleep();
        return;
    }

    // Display idle timeout (configurable, default 10s)
    if (m_backlightAwake && (now - m_lastActivityMs > DISPLAY_IDLE_TIMEOUT_MS)) {
        Serial.println("[POWER] Display idle timeout: Dimming LCD backlight to 0 on GPIO5.");
        setBacklightBrightness(0);
        m_backlightAwake = false;
    }
}

void PowerManager::enterDeepSleep() {
    setBacklightBrightness(0);
    Serial.println("[POWER] Entering deep sleep mode. Display backlight OFF on GPIO5.");
    esp_deep_sleep_start();
}
