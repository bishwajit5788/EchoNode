#include "display_manager.h"
#include "audio_manager.h"
#include "power_manager.h"
#include "sd_manager.h"
#include "bluetooth_audio.h"
#include <Wire.h>

// LVGL Draw Buffer (Allocated in PSRAM to conserve internal SRAM for audio DMA)
static lv_disp_draw_buf_t draw_buf;
static lv_color_t* buf1 = nullptr;
static lv_color_t* buf2 = nullptr;

static void my_disp_flush(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p) {
    // Flush to 360x360 ST77916 QSPI display
    lv_disp_flush_ready(disp);
}

static void my_touchpad_read(lv_indev_drv_t * indev_driver, lv_indev_data_t * data) {
    // CST816S touch on I2C (SDA=11, SCL=10, Addr=0x15)
    data->state = LV_INDEV_STATE_REL;
}

DisplayManager::DisplayManager()
    : m_screenAlpha(nullptr),
      m_screenBeta(nullptr),
      m_screenGamma(nullptr),
      m_labelTimeAlpha(nullptr),
      m_labelBatteryAlpha(nullptr),
      m_barBatteryAlpha(nullptr),
      m_labelTrackTitle(nullptr),
      m_labelPlayTime(nullptr),
      m_btnPlayPause(nullptr),
      m_labelPlayPause(nullptr),
      m_labelVolume(nullptr),
      m_labelBtStatus(nullptr),
      m_labelBtDevice(nullptr),
      m_pulseCircle(nullptr),
      m_last1HzUpdateMs(0),
      m_pulseStep(0) {}

void DisplayManager::begin() {
    initLVGL();
    buildScreenAlpha();
    buildScreenBeta();
    buildScreenGamma();

    showScreenAlpha();
    m_last1HzUpdateMs = millis();
}

void DisplayManager::initLVGL() {
    lv_init();

    // Allocate 360x40 line buffers in PSRAM
    size_t buf_size = LCD_WIDTH * 40 * sizeof(lv_color_t);
    buf1 = (lv_color_t*)ps_malloc(buf_size);
    buf2 = (lv_color_t*)ps_malloc(buf_size);

    if (!buf1) buf1 = (lv_color_t*)malloc(buf_size);
    if (!buf2) buf2 = (lv_color_t*)malloc(buf_size);

    lv_disp_draw_buf_init(&draw_buf, buf1, buf2, LCD_WIDTH * 40);

    static lv_disp_drv_t disp_drv;
    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res = LCD_WIDTH;
    disp_drv.ver_res = LCD_HEIGHT;
    disp_drv.flush_cb = my_disp_flush;
    disp_drv.draw_buf = &draw_buf;
    lv_disp_drv_register(&disp_drv);

    static lv_indev_drv_t indev_drv;
    lv_indev_drv_init(&indev_drv);
    indev_drv.type = LV_INDEV_TYPE_POINTER;
    indev_drv.read_cb = my_touchpad_read;
    lv_indev_drv_register(&indev_drv);
}

// --------------------------------------------------------------------------
// SCREEN ALPHA: Standby Dashboard
// --------------------------------------------------------------------------
void DisplayManager::buildScreenAlpha() {
    m_screenAlpha = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(m_screenAlpha, lv_color_hex(0x0A0D14), LV_PART_MAIN);

    // Circular Display Boundary Guide
    lv_obj_t* circle = lv_obj_create(m_screenAlpha);
    lv_obj_set_size(circle, 350, 350);
    lv_obj_align(circle, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_radius(circle, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_opa(circle, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_color(circle, lv_color_hex(0x1E293B), 0);
    lv_obj_set_style_border_width(circle, 2, 0);

    // Large Digital Time (Central)
    m_labelTimeAlpha = lv_label_create(m_screenAlpha);
    lv_label_set_text(m_labelTimeAlpha, "22:45");
    lv_obj_align(m_labelTimeAlpha, LV_ALIGN_CENTER, 0, -45);
    lv_obj_set_style_text_color(m_labelTimeAlpha, lv_color_hex(0xFFFFFF), 0);
    lv_obj_set_style_text_font(m_labelTimeAlpha, &lv_font_montserrat_48, 0);

    // Battery Fuel Gauge
    m_labelBatteryAlpha = lv_label_create(m_screenAlpha);
    lv_label_set_text(m_labelBatteryAlpha, "3.85V (75%)");
    lv_obj_align(m_labelBatteryAlpha, LV_ALIGN_CENTER, 0, 8);
    lv_obj_set_style_text_color(m_labelBatteryAlpha, lv_color_hex(0x94A3B8), 0);

    // Profile Button Left: Standalone SD Local Mode
    lv_obj_t* btnSD = lv_btn_create(m_screenAlpha);
    lv_obj_set_size(btnSD, 115, 48);
    lv_obj_align(btnSD, LV_ALIGN_CENTER, -65, 75);
    lv_obj_set_style_radius(btnSD, 24, 0);
    lv_obj_set_style_bg_color(btnSD, lv_color_hex(0x6366F1), 0);
    lv_obj_t* lblSD = lv_label_create(btnSD);
    lv_label_set_text(lblSD, "SD Music");
    lv_obj_center(lblSD);

    lv_obj_add_event_cb(btnSD, [](lv_event_t* e) {
        PowerManager::instance().noteUserActivity();
        AudioManager::instance().transitionTo(SystemState::LOCAL_SD_ACTIVE);
        DisplayManager::instance().showScreenBeta();
    }, LV_EVENT_CLICKED, NULL);

    // Profile Button Right: Bluetooth Mode (Capability-gated)
    lv_obj_t* btnBT = lv_btn_create(m_screenAlpha);
    lv_obj_set_size(btnBT, 115, 48);
    lv_obj_align(btnBT, LV_ALIGN_CENTER, 65, 75);
    lv_obj_set_style_radius(btnBT, 24, 0);
    lv_obj_set_style_bg_color(btnBT, lv_color_hex(0x334155), 0); // Muted style
    lv_obj_t* lblBT = lv_label_create(btnBT);
    lv_label_set_text(lblBT, "BT (N/A)");
    lv_obj_center(lblBT);

    lv_obj_add_event_cb(btnBT, [](lv_event_t* e) {
        PowerManager::instance().noteUserActivity();
        DisplayManager::instance().showScreenGamma(); // Displays hardware explanation
    }, LV_EVENT_CLICKED, NULL);
}

// --------------------------------------------------------------------------
// SCREEN BETA: Standalone Local Playback Interface (Strict 1Hz updates)
// --------------------------------------------------------------------------
void DisplayManager::buildScreenBeta() {
    m_screenBeta = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(m_screenBeta, lv_color_hex(0x0A0D14), LV_PART_MAIN);

    // Track Title (Static frame rendering)
    m_labelTrackTitle = lv_label_create(m_screenBeta);
    lv_label_set_text(m_labelTrackTitle, "Bedside Music");
    lv_label_set_long_mode(m_labelTrackTitle, LV_LABEL_LONG_DOT);
    lv_obj_set_width(m_labelTrackTitle, 280);
    lv_obj_align(m_labelTrackTitle, LV_ALIGN_CENTER, 0, -80);
    lv_obj_set_style_text_align(m_labelTrackTitle, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_set_style_text_color(m_labelTrackTitle, lv_color_hex(0xF8FAFC), 0);

    // Playback Time (Updated strictly at 1Hz to eliminate audio SPI crackle)
    m_labelPlayTime = lv_label_create(m_screenBeta);
    lv_label_set_text(m_labelPlayTime, "00:00 / 00:00");
    lv_obj_align(m_labelPlayTime, LV_ALIGN_CENTER, 0, -45);
    lv_obj_set_style_text_color(m_labelPlayTime, lv_color_hex(0x64748B), 0);

    // Prev Button
    lv_obj_t* btnPrev = lv_btn_create(m_screenBeta);
    lv_obj_set_size(btnPrev, 50, 50);
    lv_obj_align(btnPrev, LV_ALIGN_CENTER, -80, 10);
    lv_obj_set_style_radius(btnPrev, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(btnPrev, lv_color_hex(0x1E293B), 0);
    lv_obj_t* lblPrev = lv_label_create(btnPrev);
    lv_label_set_text(lblPrev, "<");
    lv_obj_center(lblPrev);
    lv_obj_add_event_cb(btnPrev, [](lv_event_t* e) {
        PowerManager::instance().noteUserActivity();
        AudioManager::instance().previousTrack();
    }, LV_EVENT_CLICKED, NULL);

    // Play/Pause Button
    m_btnPlayPause = lv_btn_create(m_screenBeta);
    lv_obj_set_size(m_btnPlayPause, 65, 65);
    lv_obj_align(m_btnPlayPause, LV_ALIGN_CENTER, 0, 10);
    lv_obj_set_style_radius(m_btnPlayPause, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(m_btnPlayPause, lv_color_hex(0x6366F1), 0);
    m_labelPlayPause = lv_label_create(m_btnPlayPause);
    lv_label_set_text(m_labelPlayPause, "||");
    lv_obj_center(m_labelPlayPause);
    lv_obj_add_event_cb(m_btnPlayPause, [](lv_event_t* e) {
        PowerManager::instance().noteUserActivity();
        AudioManager::instance().togglePlayPause();
    }, LV_EVENT_CLICKED, NULL);

    // Next Button
    lv_obj_t* btnNext = lv_btn_create(m_screenBeta);
    lv_obj_set_size(btnNext, 50, 50);
    lv_obj_align(btnNext, LV_ALIGN_CENTER, 80, 10);
    lv_obj_set_style_radius(btnNext, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(btnNext, lv_color_hex(0x1E293B), 0);
    lv_obj_t* lblNext = lv_label_create(btnNext);
    lv_label_set_text(lblNext, ">");
    lv_obj_center(lblNext);
    lv_obj_add_event_cb(btnNext, [](lv_event_t* e) {
        PowerManager::instance().noteUserActivity();
        AudioManager::instance().nextTrack();
    }, LV_EVENT_CLICKED, NULL);

    // Volume Ceiling Indicator (Max 65% safe ceiling)
    m_labelVolume = lv_label_create(m_screenBeta);
    lv_label_set_text(m_labelVolume, "Vol: 48% (Cap: 65%)");
    lv_obj_align(m_labelVolume, LV_ALIGN_CENTER, 0, 55);
    lv_obj_set_style_text_color(m_labelVolume, lv_color_hex(0x64748B), 0);

    // Return to Standby Button (Bottom boundary)
    lv_obj_t* btnBack = lv_btn_create(m_screenBeta);
    lv_obj_set_size(btnBack, 100, 36);
    lv_obj_align(btnBack, LV_ALIGN_CENTER, 0, 95);
    lv_obj_set_style_radius(btnBack, 18, 0);
    lv_obj_set_style_bg_color(btnBack, lv_color_hex(0x334155), 0);
    lv_obj_t* lblBack = lv_label_create(btnBack);
    lv_label_set_text(lblBack, "Standby");
    lv_obj_center(lblBack);
    lv_obj_add_event_cb(btnBack, [](lv_event_t* e) {
        PowerManager::instance().noteUserActivity();
        AudioManager::instance().transitionTo(SystemState::OFF);
        DisplayManager::instance().showScreenAlpha();
    }, LV_EVENT_CLICKED, NULL);
}

// --------------------------------------------------------------------------
// SCREEN GAMMA: Bluetooth Hardware Truth Status (No fake A2DP discovery)
// --------------------------------------------------------------------------
void DisplayManager::buildScreenGamma() {
    m_screenGamma = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(m_screenGamma, lv_color_hex(0x0A0D14), LV_PART_MAIN);

    // Informative Title
    lv_obj_t* title = lv_label_create(m_screenGamma);
    lv_label_set_text(title, "Bluetooth Audio\nUnavailable");
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_align(title, LV_ALIGN_CENTER, 0, -65);
    lv_obj_set_style_text_color(title, lv_color_hex(0xF43F5E), 0); // Rose red

    // Architectural Explanation
    lv_obj_t* desc = lv_label_create(m_screenGamma);
    lv_label_set_text(desc, "ESP32-S3 physically lacks\nClassic Bluetooth (BR/EDR).\nA2DP Sink is not supported.\nZero RF radiation active.");
    lv_obj_set_width(desc, 280);
    lv_obj_set_style_text_align(desc, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_align(desc, LV_ALIGN_CENTER, 0, 10);
    lv_obj_set_style_text_color(desc, lv_color_hex(0x94A3B8), 0);

    // Return to Standby Button
    lv_obj_t* btnEscape = lv_btn_create(m_screenGamma);
    lv_obj_set_size(btnEscape, 130, 42);
    lv_obj_align(btnEscape, LV_ALIGN_CENTER, 0, 95);
    lv_obj_set_style_radius(btnEscape, 21, 0);
    lv_obj_set_style_bg_color(btnEscape, lv_color_hex(0x475569), 0);
    lv_obj_t* lblEscape = lv_label_create(btnEscape);
    lv_label_set_text(lblEscape, "Back");
    lv_obj_center(lblEscape);
    lv_obj_add_event_cb(btnEscape, [](lv_event_t* e) {
        PowerManager::instance().noteUserActivity();
        DisplayManager::instance().showScreenAlpha();
    }, LV_EVENT_CLICKED, NULL);
}

void DisplayManager::showScreenAlpha() {
    lv_scr_load(m_screenAlpha);
}

void DisplayManager::showScreenBeta() {
    lv_scr_load(m_screenBeta);
}

void DisplayManager::showScreenGamma() {
    lv_scr_load(m_screenGamma);
}

void DisplayManager::updateDynamicElements() {
    unsigned long now = millis();
    if (now - m_last1HzUpdateMs >= 1000) {
        m_last1HzUpdateMs = now;

        // 1. Update Battery Display (Alpha)
        if (m_labelBatteryAlpha) {
            float v = PowerManager::instance().getBatteryVoltage();
            int pct = PowerManager::instance().getBatteryPercentage();
            char buf[32];
            snprintf(buf, sizeof(buf), "%.2fV (%d%%)", v, pct);
            lv_label_set_text(m_labelBatteryAlpha, buf);
            if (PowerManager::instance().isBatteryLow()) {
                lv_obj_set_style_text_color(m_labelBatteryAlpha, lv_color_hex(0xEF4444), 0);
            } else {
                lv_obj_set_style_text_color(m_labelBatteryAlpha, lv_color_hex(0x94A3B8), 0);
            }
        }

        // 2. Update SD Playback Time & Track (Beta)
        if (AudioManager::instance().getState() == SystemState::LOCAL_SD_ACTIVE) {
            if (m_labelPlayTime) {
                uint32_t cur = AudioManager::instance().getPlaybackTimeSec();
                uint32_t tot = AudioManager::instance().getTotalDurationSec();
                char timeBuf[32];
                snprintf(timeBuf, sizeof(timeBuf), "%02u:%02u / %02u:%02u", 
                         (cur / 60) % 60, cur % 60, 
                         (tot / 60) % 60, tot % 60);
                lv_label_set_text(m_labelPlayTime, timeBuf);
            }
            if (m_labelTrackTitle) {
                lv_label_set_text(m_labelTrackTitle, AudioManager::instance().getCurrentTrackTitle().c_str());
            }
            if (m_labelPlayPause) {
                lv_label_set_text(m_labelPlayPause, AudioManager::instance().isPlaying() ? "||" : ">");
            }
            if (m_labelVolume) {
                uint8_t vol = AudioManager::instance().getVolume();
                int pct = (vol * 100) / MAX_AUDIO_VOLUME_RAW;
                char volBuf[32];
                snprintf(volBuf, sizeof(volBuf), "Vol: %d%% (Cap: 65%%)", pct);
                lv_label_set_text(m_labelVolume, volBuf);
            }
        }
    }
}

void DisplayManager::loop() {
    lv_timer_handler();
    updateDynamicElements();
}
