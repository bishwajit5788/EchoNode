#pragma once
#include <Arduino.h>

// ==============================================================================
// ECHONODE AUTHORITATIVE HARDWARE CONFIGURATION & SAFETY POLICIES
// Target: Original Waveshare ESP32-S3-Touch-LCD-1.85 (360x360 Round Display)
// DAC: PCM5101 (3-Wire I2S with internal PLL)
// IO Expander: TCA9554 (Controls MicroSD CS via EXIO3)
// ==============================================================================

// Display Dimensions (DESIGN.md)
#define LCD_WIDTH               360
#define LCD_HEIGHT              360
#define LCD_RADIUS              180

// --- 1. LCD Interface (ST77916 QSPI) - Original Waveshare Board ---
#define LCD_DATA0_PIN           46
#define LCD_DATA1_PIN           45
#define LCD_DATA2_PIN           42
#define LCD_DATA3_PIN           41
#define LCD_SCK_PIN             40
#define LCD_CS_PIN              21
#define LCD_BL_PIN              5     // Backlight PWM control pin (GPIO5)

// --- 2. MicroSD Card SPI Interface ---
#define SD_MISO_PIN             16    // D0 / MISO
#define SD_MOSI_PIN             17    // CMD / MOSI
#define SD_SCK_PIN              14    // SCK
// MicroSD CS is controlled via TCA9554 EXIO3 (not a direct ESP32 GPIO)
#define SD_CS_EXIO_PIN          3     // EXIO3 on TCA9554
#define TCA9554_EXIO3           3

// --- 3. Shared I2C Bus ---
#define I2C_SDA_PIN             11
#define I2C_SCL_PIN             10
#define TCA9554_I2C_ADDR        0x20  // Onboard IO Expander
#define CST816S_I2C_ADDR        0x15  // Capacitive Touch Controller
#define PCF8563_I2C_ADDR        0x51  // Real-Time Clock

// --- 4. Audio I2S Core (PCM5101 DAC) ---
// PCM5101 operates in 3-wire I2S mode; internal PLL generates master clock from BCK
#define I2S_DOUT_PIN            47    // PCM5101 DIN
#define I2S_LRCK_PIN            38    // PCM5101 LRCK
#define I2S_BCLK_PIN            48    // PCM5101 BCK

// --- 5. Battery Monitoring ADC (KP 702635 600mAh 3.7V LiPo) ---
#define BATTERY_ADC_PIN         1
#define BATTERY_MIN_SAFE_V      3.50f  // 3.5V Low Battery Warning Threshold
#define BATTERY_FULL_V          4.20f
#define BATTERY_ADC_DIVIDER     2.0f   // Onboard 100k / 100k divider

// ==============================================================================
// COMPILE-TIME CONFIGURABLE SAFETY & POLICY DIRECTIVES (RULES.md)
// ==============================================================================

// RULE_VOLUME_CEILING: Digital volume hard-capped at <= 65%
#define MAX_AUDIO_VOLUME_RAW    21
#define SAFE_VOLUME_CEILING_PCT 65
#define HARD_MAX_VOLUME_LEVEL   14     // 14 / 21 = 66.6% ceiling

// RULE_THERMAL_SHUTDOWN: 30 minutes continuous audio without input (bedding safety)
#ifndef INACTIVITY_TIMEOUT_MS
#define INACTIVITY_TIMEOUT_MS   (30UL * 60UL * 1000UL) // 30 minutes
#endif

// Display Backlight Idle Timeout: 10 seconds of user inactivity
#ifndef DISPLAY_IDLE_TIMEOUT_MS
#define DISPLAY_IDLE_TIMEOUT_MS (10UL * 1000UL)        // 10 seconds
#endif

// Legacy alias compatibility
#define THERMAL_SLEEP_TIMEOUT_MS  INACTIVITY_TIMEOUT_MS
#define BACKLIGHT_IDLE_TIMEOUT_MS DISPLAY_IDLE_TIMEOUT_MS
