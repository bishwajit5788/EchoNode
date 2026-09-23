#pragma once
#include <Arduino.h>
#include <lvgl.h>
#include "config.h"

class DisplayManager {
public:
    static DisplayManager& instance() {
        static DisplayManager inst;
        return inst;
    }

    void begin();
    void loop();

    void showScreenAlpha();  // Standby Dashboard
    void showScreenBeta();   // Standalone SD Playback
    void showScreenGamma();  // Bluetooth Audio Sync

    void updateDynamicElements(); // 1Hz update loop

private:
    DisplayManager();

    void initLVGL();
    void buildScreenAlpha();
    void buildScreenBeta();
    void buildScreenGamma();

    // Screens
    lv_obj_t* m_screenAlpha;
    lv_obj_t* m_screenBeta;
    lv_obj_t* m_screenGamma;

    // Alpha elements
    lv_obj_t* m_labelTimeAlpha;
    lv_obj_t* m_labelBatteryAlpha;
    lv_obj_t* m_barBatteryAlpha;

    // Beta elements (SD playback)
    lv_obj_t* m_labelTrackTitle;
    lv_obj_t* m_labelPlayTime;
    lv_obj_t* m_btnPlayPause;
    lv_obj_t* m_labelPlayPause;
    lv_obj_t* m_labelVolume;

    // Gamma elements (Bluetooth)
    lv_obj_t* m_labelBtStatus;
    lv_obj_t* m_labelBtDevice;
    lv_obj_t* m_pulseCircle;

    unsigned long m_last1HzUpdateMs;
    uint8_t m_pulseStep;
};
