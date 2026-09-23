#pragma once
#include <Arduino.h>

// ==============================================================================
// ECHONODE HARDWARE CONFIGURATION & SAFETY POLICIES
// Target: Waveshare ESP32-S3 1.85-inch Round LCD (360x360)
// ==============================================================================

// Display Dimensions (DESIGN.md)
#define LCD_WIDTH               360
#define LCD_HEIGHT              360
#define LCD_RADIUS              180

// Pinout Mapping - Waveshare ESP32-S3 1.85" Display & I2S Audio
#define LCD_BL_PIN              6     // Backlight PWM pin
#define LCD_CS_PIN              10
#define LCD_DC_PIN              8
#define LCD_RST_PIN             9
#define LCD_SCK_PIN             12
#define LCD_MOSI_PIN            11

// Touch Panel - CST816S (I2C)
#define TOUCH_SDA_PIN           4
#define TOUCH_SCL_PIN           5
#define TOUCH_INT_PIN           7
#define TOUCH_RST_PIN           13

// MicroSD Card SPI Interface
#define SD_CS_PIN               14
#define SD_SCK_PIN              15
#define SD_MOSI_PIN             16
#define SD_MISO_PIN             17

// Audio I2S Core (ES8311 / PCM5101 / MAX98357A)
#define I2S_BCLK_PIN            39
#define I2S_LRCK_PIN            38
#define I2S_DOUT_PIN            40
#define I2S_MCLK_PIN            2     // Master clock if codec requires it
#define I2S_PA_EN_PIN           41    // External power amplifier enable pin (active HIGH)

// Battery Monitoring ADC (KP 702635 600mAh 3.7V LiPo)
#define BATTERY_ADC_PIN         1
#define BATTERY_MIN_SAFE_V      3.50f  // 3.5V Low Battery Warning Threshold
#define BATTERY_FULL_V          4.20f
#define BATTERY_ADC_DIVIDER     2.0f   // Voltage divider on board (100k / 100k)

// ==============================================================================
// FIRMWARE SAFETY RULES (RULES.md)
// ==============================================================================

// RULE_VOLUME_CEILING: Hard-cap digital volume to 65% of hardware maximum
// In ESP32-audioI2S, volume ranges 0-21. Max safe level = 14 (66%)
#define MAX_AUDIO_VOLUME_RAW    21
#define SAFE_VOLUME_CEILING_PCT 65
#define HARD_MAX_VOLUME_LEVEL   14     // 14/21 = 66.6%

// RULE_THERMAL_SHUTDOWN: 30 minutes continuous audio without input
#define THERMAL_SLEEP_TIMEOUT_MS (30UL * 60UL * 1000UL) // 30 minutes

// Display Idle Backlight Sleep: 10 seconds of user inactivity
#define BACKLIGHT_IDLE_TIMEOUT_MS (10UL * 1000UL)        // 10 seconds

// Operating Profiles
enum class OperationalMode {
    STANDBY = 0,
    SD_LOCAL_PLAYBACK = 1,
    BLUETOOTH_A2DP_SINK = 2
};
