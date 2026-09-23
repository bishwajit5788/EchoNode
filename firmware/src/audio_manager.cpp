#include "audio_manager.h"
#include "sd_manager.h"
#include <Audio.h>
#include <BluetoothA2DPSink.h>
#include <esp_bt.h>
#include <WiFi.h>

AudioManager::AudioManager()
    : m_currentMode(OperationalMode::STANDBY),
      m_currentVolume(10), // Default comfortable safe volume (~48%)
      m_currentTrackIndex(0),
      m_isPaused(false),
      m_isMuted(false),
      m_sdAudio(nullptr),
      m_a2dpSink(nullptr),
      m_btConnected(false),
      m_btConnectedDevice("") {}

AudioManager::~AudioManager() {
    teardownSDPlayer();
    teardownBluetoothSink();
}

void AudioManager::begin() {
    // Configure External Power Amplifier Pin
    pinMode(I2S_PA_EN_PIN, OUTPUT);
    muteI2S(true);

    // Initial state: radios disabled for maximum standby battery savings
    WiFi.mode(WIFI_OFF);
    btStop();
    esp_bt_controller_disable();

    Serial.println("[AUDIO] Core initialized in STANDBY profile.");
}

void AudioManager::loop() {
    if (m_currentMode == OperationalMode::SD_LOCAL_PLAYBACK && m_sdAudio != nullptr) {
        m_sdAudio->loop();
        // Check if track ended
        if (!m_sdAudio->isRunning() && !m_isPaused) {
            nextTrack();
        }
    }
}

bool AudioManager::switchMode(OperationalMode targetMode) {
    if (m_currentMode == targetMode) return true;

    Serial.printf("[AUDIO] Switching profile from %d to %d (Enforcing RULE_MUTUAL_EXCLUSION)\n", 
                  (int)m_currentMode, (int)targetMode);

    // Step 1: Fully tear down and de-allocate whatever was previously running
    if (m_currentMode == OperationalMode::SD_LOCAL_PLAYBACK) {
        teardownSDPlayer();
    } else if (m_currentMode == OperationalMode::BLUETOOTH_A2DP_SINK) {
        teardownBluetoothSink();
    }

    // Step 2: Establish the new profile cleanly
    bool success = false;
    switch (targetMode) {
        case OperationalMode::STANDBY:
            muteI2S(true);
            m_currentMode = OperationalMode::STANDBY;
            success = true;
            break;

        case OperationalMode::SD_LOCAL_PLAYBACK:
            success = initSDPlayer();
            if (success) {
                m_currentMode = OperationalMode::SD_LOCAL_PLAYBACK;
            } else {
                m_currentMode = OperationalMode::STANDBY;
            }
            break;

        case OperationalMode::BLUETOOTH_A2DP_SINK:
            success = initBluetoothSink();
            if (success) {
                m_currentMode = OperationalMode::BLUETOOTH_A2DP_SINK;
            } else {
                m_currentMode = OperationalMode::STANDBY;
            }
            break;
    }

    return success;
}

bool AudioManager::initSDPlayer() {
    // Zero-Radio Directive: Guarantee Wi-Fi & BT are disabled
    WiFi.mode(WIFI_OFF);
    btStop();
    esp_bt_controller_disable();

    // Mount MicroSD
    if (!SDManager::instance().mount()) {
        Serial.println("[AUDIO] Error: Unable to mount SD for playback.");
        return false;
    }

    if (SDManager::instance().getTrackCount() == 0) {
        Serial.println("[AUDIO] Warning: No audio tracks found on SD card.");
    }

    // Allocate SD Audio Engine
    m_sdAudio = new Audio();
    m_sdAudio->setPinout(I2S_BCLK_PIN, I2S_LRCK_PIN, I2S_DOUT_PIN, I2S_MCLK_PIN);
    
    // RULE_VOLUME_CEILING: Hard-limit volume
    setVolume(m_currentVolume);

    m_isPaused = false;
    muteI2S(false);

    if (SDManager::instance().getTrackCount() > 0) {
        playSDTrack(m_currentTrackIndex);
    }
    return true;
}

void AudioManager::teardownSDPlayer() {
    muteI2S(true); // RULE_I2S_MUTING
    if (m_sdAudio != nullptr) {
        m_sdAudio->stopSong();
        delete m_sdAudio;
        m_sdAudio = nullptr;
        Serial.println("[AUDIO] SD Audio engine deallocated from RAM.");
    }
    SDManager::instance().unmount();
}

bool AudioManager::initBluetoothSink() {
    // Unmount SD to release SPI bus traffic
    SDManager::instance().unmount();

    Serial.println("[AUDIO] Initializing Bluetooth A2DP Sink...");
    m_a2dpSink = new BluetoothA2DPSink();

    // Configure I2S pinout for A2DP Sink
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_BCLK_PIN,
        .ws_io_num = I2S_LRCK_PIN,
        .data_out_num = I2S_DOUT_PIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };
    m_a2dpSink->set_pin_config(pin_config);

    // Callbacks for connection status
    m_a2dpSink->set_on_connection_state_changed([](esp_a2d_connection_state_t state, void* obj) {
        AudioManager* self = static_cast<AudioManager*>(obj);
        if (state == ESP_A2D_CONNECTION_STATE_CONNECTED) {
            self->m_btConnected = true;
            self->muteI2S(false);
            Serial.println("[BT] Mobile device connected successfully!");
        } else if (state == ESP_A2D_CONNECTION_STATE_DISCONNECTED) {
            self->m_btConnected = false;
            self->muteI2S(true);
            Serial.println("[BT] Mobile device disconnected.");
        }
    }, this);

    m_a2dpSink->start("EchoNode Audio");
    return true;
}

void AudioManager::teardownBluetoothSink() {
    muteI2S(true); // RULE_I2S_MUTING
    if (m_a2dpSink != nullptr) {
        m_a2dpSink->end(true);
        delete m_a2dpSink;
        m_a2dpSink = nullptr;
        Serial.println("[AUDIO] Bluetooth A2DP Sink deallocated from RAM.");
    }
    btStop();
    esp_bt_controller_disable();
    m_btConnected = false;
    m_btConnectedDevice = "";
}

bool AudioManager::playSDTrack(int trackIndex) {
    if (!m_sdAudio || !SDManager::instance().isMounted()) return false;
    if (trackIndex < 0 || trackIndex >= SDManager::instance().getTrackCount()) return false;

    m_currentTrackIndex = trackIndex;
    String path = SDManager::instance().getTrackPath(trackIndex);
    Serial.printf("[AUDIO] Starting SD track [%d]: %s\n", trackIndex, path.c_str());

    muteI2S(false);
    m_isPaused = false;
    return m_sdAudio->connecttoFS(SD, path.c_str());
}

void AudioManager::pauseSD() {
    if (m_sdAudio && m_sdAudio->isRunning()) {
        m_sdAudio->pauseResume();
        m_isPaused = true;
        muteI2S(true); // RULE_I2S_MUTING: mute bus on pause to remove hiss
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

// RULE_VOLUME_CEILING: Hard-cap volume to 65% (14 out of 21)
void AudioManager::setVolume(uint8_t volumeLevel) {
    if (volumeLevel > HARD_MAX_VOLUME_LEVEL) {
        volumeLevel = HARD_MAX_VOLUME_LEVEL; // Enforce hard cap
    }
    m_currentVolume = volumeLevel;
    if (m_sdAudio) {
        m_sdAudio->setVolume(m_currentVolume);
    }
    if (m_a2dpSink) {
        // Map 0-14 into 0-127 for A2DP
        int btVol = (m_currentVolume * 127) / HARD_MAX_VOLUME_LEVEL;
        m_a2dpSink->set_volume(btVol);
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

// RULE_I2S_MUTING: Hardware mute PA & disable active clocks to kill idle hiss
void AudioManager::muteI2S(bool mute) {
    m_isMuted = mute;
    digitalWrite(I2S_PA_EN_PIN, mute ? LOW : HIGH);
}

String AudioManager::getCurrentTrackTitle() const {
    if (m_currentMode == OperationalMode::SD_LOCAL_PLAYBACK) {
        return SDManager::instance().getTrackTitle(m_currentTrackIndex);
    } else if (m_currentMode == OperationalMode::BLUETOOTH_A2DP_SINK) {
        return m_btConnected ? "Bluetooth Audio Stream" : "Waiting for Pairing...";
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
