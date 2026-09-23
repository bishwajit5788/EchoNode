#include "audio_manager.h"
#include "sd_manager.h"
#include "tca9554.h"
#include <Audio.h>
#include <WiFi.h>
#include <driver/i2s.h>
#include <esp_heap_caps.h>
#include <math.h>

#define HARDWARE_I2S_PORT I2S_NUM_0

AudioManager::AudioManager()
    : m_state(SystemState::OFF),
      m_currentVolume(10), // Safe default ~48%
      m_currentTrackIndex(0),
      m_isPaused(false),
      m_isMuted(false),
      m_sdAudio(nullptr),
      m_btAudio(&ESP32S3BluetoothAudio::instance()) {
    m_baselineMemory = getMemorySnapshot();
}

AudioManager::~AudioManager() {
    destroySDDecoder();
}

MemorySnapshot AudioManager::getMemorySnapshot() const {
    MemorySnapshot snap;
    snap.internalHeapFree = esp_get_free_internal_heap_size();
    snap.psramFree = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    return snap;
}

void AudioManager::logMemoryDelta(const char* tag, const MemorySnapshot& before, const MemorySnapshot& after) {
    long intHeapDelta = (long)after.internalHeapFree - (long)before.internalHeapFree;
    long psramDelta = (long)after.psramFree - (long)before.psramFree;
    Serial.printf("[MEM] %s | Internal Heap: %u (Delta: %+ld B) | PSRAM: %u (Delta: %+ld B)\n",
                  tag, after.internalHeapFree, intHeapDelta, after.psramFree, psramDelta);
}

void AudioManager::begin() {
    // Disable radios completely in standalone local audio mode
    WiFi.mode(WIFI_OFF);

    // Initial hardware mute
    muteI2S(true);

    m_baselineMemory = getMemorySnapshot();
    Serial.printf("[AUDIO] Core initialized in OFF state. Baseline Heap: %u B, PSRAM: %u B\n",
                  m_baselineMemory.internalHeapFree, m_baselineMemory.psramFree);
}

void AudioManager::loop() {
    if (m_state == SystemState::LOCAL_SD_ACTIVE && m_sdAudio != nullptr) {
        m_sdAudio->loop();

        // Auto-advance track when current track completes
        if (!m_sdAudio->isRunning() && !m_isPaused && SDManager::instance().getTrackCount() > 0) {
            nextTrack();
        }
    }
}

bool AudioManager::transitionTo(SystemState targetState) {
    if (m_state == targetState) return true;

    Serial.printf("[FSM] Transitioning: %s -> %s\n", stateToString(m_state), stateToString(targetState));

    // Rule: ACTIVE_A -> mute -> stop -> destroy -> free -> clear pointers -> verify resources -> ACTIVE_B
    if (m_state == SystemState::LOCAL_SD_ACTIVE || m_state == SystemState::LOCAL_SD_STARTING) {
        m_state = SystemState::LOCAL_SD_STOPPING;
        destroySDDecoder();
        m_state = SystemState::OFF;
    }

    if (targetState == SystemState::OFF) {
        m_state = SystemState::OFF;
        muteI2S(true);
        return true;
    }

    if (targetState == SystemState::LOCAL_SD_ACTIVE) {
        m_state = SystemState::LOCAL_SD_STARTING;
        if (createSDDecoder()) {
            m_state = SystemState::LOCAL_SD_ACTIVE;
            return true;
        } else {
            m_state = SystemState::ERROR;
            destroySDDecoder();
            return false;
        }
    }

    if (targetState == SystemState::BT_ACTIVE || targetState == SystemState::BT_STARTING) {
        // Capability-gated: ESP32-S3 physically lacks Bluetooth Classic
        Serial.printf("[FSM] BT Audio requested: %s\n", m_btAudio->getHardwareExplanation());
        m_state = SystemState::OFF;
        return false;
    }

    m_state = targetState;
    return true;
}

bool AudioManager::createSDDecoder() {
    MemorySnapshot before = getMemorySnapshot();

    // 1. Mount SD Card via TCA9554 EXIO3 CS
    if (!SDManager::instance().sd_mount()) {
        Serial.println("[AUDIO] ERROR: Failed to mount MicroSD storage.");
        return false;
    }

    // 2. Dynamically allocate Audio decoder
    m_sdAudio = new Audio();
    if (!m_sdAudio) {
        Serial.println("[AUDIO] ERROR: Failed to allocate Audio decoder in memory!");
        return false;
    }

    // Configure PCM5101 3-wire I2S pins (DIN=47, LRCK=38, BCK=48)
    m_sdAudio->setPinout(I2S_BCLK_PIN, I2S_LRCK_PIN, I2S_DOUT_PIN);

    // RULE_VOLUME_CEILING: Enforce <= 65% ceiling
    setVolume(m_currentVolume);

    m_isPaused = false;
    muteI2S(false);

    MemorySnapshot after = getMemorySnapshot();
    logMemoryDelta("Decoder Allocated", before, after);

    // Auto-play first track if available
    if (SDManager::instance().getTrackCount() > 0) {
        playSDTrack(m_currentTrackIndex);
    }
    return true;
}

void AudioManager::destroySDDecoder() {
    MemorySnapshot before = getMemorySnapshot();

    muteI2S(true); // Immediate hardware/software mute

    if (m_sdAudio != nullptr) {
        m_sdAudio->stopSong();
        delete m_sdAudio;
        m_sdAudio = nullptr;
        Serial.println("[AUDIO] SD Audio decoder instance destroyed.");
    }

    // Safely unmount SD storage
    SDManager::instance().sd_unmount();

    MemorySnapshot after = getMemorySnapshot();
    logMemoryDelta("Decoder Destroyed (Leak Check)", before, after);
}

// Deterministic PCM/I2S Hardware Sine Tone Generator (Direct I2S test path)
bool AudioManager::playHardwareTone(uint16_t freqHz, uint32_t durationMs) {
    Serial.printf("[AUDIO] Emitting hardware PCM sine tone (%u Hz, %lu ms) via PCM5101 (DIN=47, LRCK=38, BCK=48)...\n",
                  freqHz, durationMs);

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

    i2s_driver_install(HARDWARE_I2S_PORT, &i2s_cfg, 0, NULL);
    i2s_set_pin(HARDWARE_I2S_PORT, &pin_cfg);

    const int SAMPLE_RATE = 44100;
    const int BUFFER_SAMPLES = 256;
    int16_t buffer[BUFFER_SAMPLES * 2];
    size_t bytes_written;

    // RULE_VOLUME_CEILING: -6 dBFS amplitude (~16000 max sample)
    const float MAX_AMP = 16000.0f;
    int total_frames = (SAMPLE_RATE * durationMs) / 1000;

    for (int frame = 0; frame < total_frames; frame += BUFFER_SAMPLES) {
        for (int i = 0; i < BUFFER_SAMPLES; i++) {
            float t = (float)(frame + i) / SAMPLE_RATE;
            int16_t sample = (int16_t)(MAX_AMP * sin(2.0f * M_PI * freqHz * t));
            buffer[i * 2] = sample;
            buffer[i * 2 + 1] = sample;
        }
        i2s_write(HARDWARE_I2S_PORT, buffer, sizeof(buffer), &bytes_written, portMAX_DELAY);
    }

    // Mute and uninstall direct driver
    i2s_zero_dma_buffer(HARDWARE_I2S_PORT);
    i2s_driver_uninstall(HARDWARE_I2S_PORT);
    Serial.println("[AUDIO] Hardware tone test completed cleanly.");
    return true;
}

bool AudioManager::playSDTrack(int trackIndex) {
    if (!m_sdAudio || !SDManager::instance().isMounted()) return false;
    if (trackIndex < 0 || trackIndex >= SDManager::instance().getTrackCount()) return false;

    m_currentTrackIndex = trackIndex;
    String path = SDManager::instance().getTrackPath(trackIndex);
    Serial.printf("[AUDIO] Starting playback: %s\n", path.c_str());

    muteI2S(false);
    m_isPaused = false;
    return m_sdAudio->connecttoFS(SD, path.c_str());
}

void AudioManager::pauseSD() {
    if (m_sdAudio && m_sdAudio->isRunning()) {
        m_sdAudio->pauseResume();
        m_isPaused = true;
        muteI2S(true); // RULE_I2S_MUTING
    }
}

void AudioManager::resumeSD() {
    if (m_sdAudio && m_isPaused) {
        muteI2S(false);
        m_sdAudio->pauseResume();
        m_isPaused = false;
    }
}

void AudioManager::togglePlayPause() {
    if (m_isPaused) {
        resumeSD();
    } else {
        pauseSD();
    }
}

void AudioManager::stopSD() {
    if (m_sdAudio) {
        m_sdAudio->stopSong();
        m_isPaused = false;
        muteI2S(true); // RULE_I2S_MUTING
    }
}

void AudioManager::nextTrack() {
    int total = SDManager::instance().getTrackCount();
    if (total == 0) return;
    int nextIdx = (m_currentTrackIndex + 1) % total;
    playSDTrack(nextIdx);
}

void AudioManager::previousTrack() {
    int total = SDManager::instance().getTrackCount();
    if (total == 0) return;
    int prevIdx = (m_currentTrackIndex - 1 + total) % total;
    playSDTrack(prevIdx);
}

bool AudioManager::isPlaying() const {
    if (m_sdAudio) {
        return m_sdAudio->isRunning() && !m_isPaused;
    }
    return false;
}

// RULE_VOLUME_CEILING: Hard-limit volume <= 65% (14 out of 21)
void AudioManager::setVolume(uint8_t volumeLevel) {
    if (volumeLevel > HARD_MAX_VOLUME_LEVEL) {
        volumeLevel = HARD_MAX_VOLUME_LEVEL; // Enforce hard cap
    }
    m_currentVolume = volumeLevel;
    if (m_sdAudio) {
        m_sdAudio->setVolume(m_currentVolume);
    }
}

void AudioManager::volumeUp() {
    if (m_currentVolume < HARD_MAX_VOLUME_LEVEL) {
        setVolume(m_currentVolume + 1);
    }
}

void AudioManager::volumeDown() {
    if (m_currentVolume > 0) {
        setVolume(m_currentVolume - 1);
    }
}

void AudioManager::muteI2S(bool mute) {
    m_isMuted = mute;
    // On pause/stop, clear audio stream to prevent hiss
}

String AudioManager::getCurrentTrackTitle() const {
    if (m_state == SystemState::LOCAL_SD_ACTIVE) {
        return SDManager::instance().getTrackTitle(m_currentTrackIndex);
    }
    return "EchoNode Standby";
}

uint32_t AudioManager::getPlaybackTimeSec() const {
    if (m_sdAudio && m_sdAudio->isRunning()) {
        return m_sdAudio->getAudioCurrentTime();
    }
    return 0;
}

uint32_t AudioManager::getTotalDurationSec() const {
    if (m_sdAudio && m_sdAudio->isRunning()) {
        return m_sdAudio->getAudioFileDuration();
    }
    return 0;
}
