#pragma once
#include "config.h"

class PowerManager {
public:
    static PowerManager& instance() {
        static PowerManager inst;
        return inst;
    }

    void begin();
    void update();
    void noteUserActivity();

    float getBatteryVoltage();
    int getBatteryPercentage();
    bool isBatteryLow();

    void setBacklightBrightness(uint8_t brightness);
    void enterDeepSleep();
    bool isBacklightAwake() const { return m_backlightAwake; }

private:
    PowerManager();
    unsigned long m_lastActivityMs;
    unsigned long m_audioPlaybackStartMs;
    bool m_backlightAwake;
    uint8_t m_currentBrightness;
};
