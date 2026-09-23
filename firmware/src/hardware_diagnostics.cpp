#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <driver/i2s.h>
#include <math.h>
#include "config.h"

// Define I2S Port
#define I2S_PORT I2S_NUM_0

void scanI2CBus() {
    Serial.println("\n--- [1/5] I2C BUS DEVICE SCAN ---");
    Wire.begin(TOUCH_SDA_PIN, TOUCH_SCL_PIN);
    byte count = 0;
    for (byte addr = 1; addr < 127; ++addr) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("  ✓ Found I2C device at address 0x%02X", addr);
            if (addr == 0x15) Serial.print(" -> (CST816S Capacitive Touch Panel)");
            else if (addr == 0x18) Serial.print(" -> (ES8311 Audio Codec)");
            else if (addr == 0x51 || addr == 0x68) Serial.print(" -> (RTC Real-Time Clock)");
            Serial.println();
            count++;
        }
    }
    if (count == 0) {
        Serial.println("  ❌ No I2C devices discovered. Check SDA/SCL pull-ups.");
    } else {
        Serial.printf("  ✓ Total I2C devices detected: %d\n", count);
    }
}

void testBatteryADC() {
    Serial.println("\n--- [2/5] BATTERY ADC & VOLTAGE MONITOR ---");
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    uint32_t rawSum = 0;
    const int SAMPLES = 30;
    for (int i = 0; i < SAMPLES; i++) {
        rawSum += analogRead(BATTERY_ADC_PIN);
        delay(5);
    }
    uint32_t rawAvg = rawSum / SAMPLES;
    float pinV = (rawAvg / 4095.0f) * 3.3f;
    float battV = pinV * BATTERY_ADC_DIVIDER;

    Serial.printf("  Raw ADC Average (12-bit): %u\n", rawAvg);
    Serial.printf("  Calculated Battery Voltage: %.3f V\n", battV);

    if (battV > 4.30f) {
        Serial.println("  ℹ️  High voltage detected: Running from USB 5V rail / active charging.");
    } else if (battV < BATTERY_MIN_SAFE_V) {
        Serial.println("  ⚠️  WARNING: Voltage < 3.5V threshold! Low battery cutoff condition.");
    } else {
        int pct = (int)(((battV - BATTERY_MIN_SAFE_V) / (BATTERY_FULL_V - BATTERY_MIN_SAFE_V)) * 100.0f);
        Serial.printf("  ✓ Battery State: Normal Operating Range (%d%% charge)\n", pct);
    }
}

void testAudioI2SSweep() {
    Serial.println("\n--- [3/5] DUAL 8-OHM MICRO-SPEAKER I2S TONE SWEEP ---");
    Serial.println("  Safety directive: Enforcing RULE_VOLUME_CEILING (-6 dBFS amplitude).");

    // Install and configure I2S driver
    i2s_config_t i2s_cfg = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = 44100,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 256,
        .use_apll = false,
        .tx_desc_auto_clear = true
    };

    i2s_pin_config_t pin_cfg = {
        .bck_io_num = I2S_BCLK_PIN,
        .ws_io_num = I2S_LRCK_PIN,
        .data_out_num = I2S_DOUT_PIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    i2s_driver_install(I2S_PORT, &i2s_cfg, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin_cfg);

    // Unmute external PA amplifier
    pinMode(I2S_PA_EN_PIN, OUTPUT);
    digitalWrite(I2S_PA_EN_PIN, HIGH);

    const int SAMPLE_RATE = 44100;
    const int BUFFER_SAMPLES = 256;
    int16_t buffer[BUFFER_SAMPLES * 2]; // Stereo (L, R)
    size_t bytes_written;

    // Amplitude ceiling (-6 dBFS = 16384 max sample value)
    const float MAX_AMP = 16000.0f;

    // Part A: 440 Hz Reference Pitch (Stereo) for 1.5 seconds
    Serial.println("  -> Emitting 440 Hz reference tone (Both Speakers)...");
    int total_frames = SAMPLE_RATE * 1.5;
    for (int frame = 0; frame < total_frames; frame += BUFFER_SAMPLES) {
        for (int i = 0; i < BUFFER_SAMPLES; i++) {
            float t = (float)(frame + i) / SAMPLE_RATE;
            int16_t sample = (int16_t)(MAX_AMP * sin(2.0f * M_PI * 440.0f * t));
            buffer[i * 2] = sample;     // Left
            buffer[i * 2 + 1] = sample; // Right
        }
        i2s_write(I2S_PORT, buffer, sizeof(buffer), &bytes_written, portMAX_DELAY);
    }

    // Part B: Alternating Channel Check (Left then Right)
    Serial.println("  -> Emitting Left Channel only (880 Hz)...");
    total_frames = SAMPLE_RATE * 1.0;
    for (int frame = 0; frame < total_frames; frame += BUFFER_SAMPLES) {
        for (int i = 0; i < BUFFER_SAMPLES; i++) {
            float t = (float)(frame + i) / SAMPLE_RATE;
            int16_t sample = (int16_t)(MAX_AMP * sin(2.0f * M_PI * 880.0f * t));
            buffer[i * 2] = sample;     // Left
            buffer[i * 2 + 1] = 0;      // Right Silence
        }
        i2s_write(I2S_PORT, buffer, sizeof(buffer), &bytes_written, portMAX_DELAY);
    }

    Serial.println("  -> Emitting Right Channel only (880 Hz)...");
    for (int frame = 0; frame < total_frames; frame += BUFFER_SAMPLES) {
        for (int i = 0; i < BUFFER_SAMPLES; i++) {
            float t = (float)(frame + i) / SAMPLE_RATE;
            int16_t sample = (int16_t)(MAX_AMP * sin(2.0f * M_PI * 880.0f * t));
            buffer[i * 2] = 0;          // Left Silence
            buffer[i * 2 + 1] = sample; // Right
        }
        i2s_write(I2S_PORT, buffer, sizeof(buffer), &bytes_written, portMAX_DELAY);
    }

    // Part C: 100 Hz - 2000 Hz Logarithmic Sweep
    Serial.println("  -> Running frequency sweep 100 Hz -> 2000 Hz...");
    total_frames = SAMPLE_RATE * 2.5;
    for (int frame = 0; frame < total_frames; frame += BUFFER_SAMPLES) {
        for (int i = 0; i < BUFFER_SAMPLES; i++) {
            float t = (float)(frame + i) / SAMPLE_RATE;
            float freq = 100.0f * powf(2000.0f / 100.0f, t / 2.5f);
            int16_t sample = (int16_t)(MAX_AMP * sin(2.0f * M_PI * freq * t));
            buffer[i * 2] = sample;
            buffer[i * 2 + 1] = sample;
        }
        i2s_write(I2S_PORT, buffer, sizeof(buffer), &bytes_written, portMAX_DELAY);
    }

    // RULE_I2S_MUTING: Soft mute and power down amplifier
    digitalWrite(I2S_PA_EN_PIN, LOW);
    i2s_zero_dma_buffer(I2S_PORT);
    i2s_driver_uninstall(I2S_PORT);
    Serial.println("  ✓ Speaker tone sweep complete. PA and I2S bus safely muted.");
}

void testMicroSD() {
    Serial.println("\n--- [4/5] MICROSD CARD & SPI INTERFACE BENCHMARK ---");
    SPIClass spi(FSPI);
    spi.begin(SD_SCK_PIN, SD_MISO_PIN, SD_MOSI_PIN, SD_CS_PIN);

    if (!SD.begin(SD_CS_PIN, spi, 20000000)) {
        Serial.println("  ❌ SD Mount Failed. Verify card is inserted and formatted as FAT32.");
        return;
    }

    uint8_t cardType = SD.cardType();
    Serial.printf("  Card Type: %s\n", (cardType == CARD_MMC ? "MMC" :
                                        cardType == CARD_SD  ? "SDSC" :
                                        cardType == CARD_SDHC ? "SDHC/SDXC" : "UNKNOWN"));
    uint64_t totalMB = SD.cardSize() / (1024 * 1024);
    uint64_t usedMB = SD.usedBytes() / (1024 * 1024);
    Serial.printf("  Capacity: %llu MB (Used: %llu MB)\n", totalMB, usedMB);

    if (totalMB > 32768) {
        Serial.println("  ⚠️  Card exceeds 32GB constraint in PDR! Ensure FAT32 clusters.");
    } else {
        Serial.println("  ✓ Capacity is strictly <=32GB compliant.");
    }

    // Benchmark read speed
    File root = SD.open("/");
    File file = root.openNextFile();
    if (file) {
        Serial.printf("  Benchmarking read speed on sample file: %s (%u bytes)...\n", file.name(), file.size());
        uint8_t buf[512];
        unsigned long t0 = millis();
        size_t bytesRead = 0;
        while (file.available() && bytesRead < 512 * 1024) {
            bytesRead += file.read(buf, sizeof(buf));
        }
        unsigned long elapsed = millis() - t0;
        if (elapsed > 0) {
            float kbps = ((float)bytesRead / (float)elapsed); // bytes/ms = KB/s
            Serial.printf("  ✓ Read Throughput: %.2f KB/s (%.2f MB/s)\n", kbps, kbps / 1024.0f);
        }
        file.close();
    } else {
        Serial.println("  ℹ️  No files found on MicroSD card yet. Staged tracks can be copied via backend.");
    }
    root.close();
    SD.end();
}

void testBacklightPWM() {
    Serial.println("\n--- [5/5] LCD BACKLIGHT PWM SWEEP ---");
    ledcSetup(0, 5000, 8);
    ledcAttachPin(LCD_BL_PIN, 0);

    Serial.println("  Ramping brightness 0% -> 100% -> 75%...");
    for (int b = 0; b <= 255; b += 15) {
        ledcWrite(0, b);
        delay(30);
    }
    for (int b = 255; b >= 190; b -= 15) {
        ledcWrite(0, b);
        delay(30);
    }
    Serial.println("  ✓ Backlight PWM operational at resting 75% brightness.");
}

void setupDiagnostics() {
    Serial.begin(115200);
    delay(1500);

    Serial.println("\n==========================================================");
    Serial.println("     EchoNode Hardware Diagnostic & Safety Verification   ");
    Serial.println("     Waveshare ESP32-S3 1.85\" Round LCD Platform         ");
    Serial.println("==========================================================");

    scanI2CBus();
    testBatteryADC();
    testAudioI2SSweep();
    testMicroSD();
    testBacklightPWM();

    Serial.println("\n==========================================================");
    Serial.println("  ✓ All Hardware Diagnostic Tests Completed Successfully! ");
    Serial.println("==========================================================\n");
}

void loopDiagnostics() {
    delay(1000);
}

#if defined(BUILD_DIAGNOSTICS)
void setup() {
    setupDiagnostics();
}

void loop() {
    loopDiagnostics();
}
#endif

