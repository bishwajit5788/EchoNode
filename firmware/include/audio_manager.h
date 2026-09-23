#pragma once
#include <Arduino.h>
#include "config.h"

class Audio; // Forward declare ESP32-audioI2S Audio class
class BluetoothA2DPSink; // Forward declare ESP32-A2DP class

class AudioManager {
public:
    static AudioManager& instance() {
        static AudioManager inst;
        return inst;
    }

    void begin();
    void loop();

    // Profile Switching with RULE_MUTUAL_EXCLUSION
    bool switchMode(OperationalMode targetMode);
    OperationalMode getCurrentMode() const { return m_currentMode; }

    // Standalone SD Playback Controls
    bool playSDTrack(int trackIndex);
    void pauseSD();
    void resumeSD();
    void togglePlayPause();
    void stopSD();
    void nextTrack();
    void previousTrack();
    bool isPlaying() const;

    // Volume Control with RULE_VOLUME_CEILING
    void setVolume(uint8_t volumeLevel);
    uint8_t getVolume() const { return m_currentVolume; }
    void volumeUp();
    void volumeDown();

    // Hardware / Code-level Muting (RULE_I2S_MUTING)
    void muteI2S(bool mute);

    // Audio Metadata / Status
    String getCurrentTrackTitle() const;
    uint32_t getPlaybackTimeSec() const;
    uint32_t getTotalDurationSec() const;
    String getBluetoothDeviceName() const { return m_btConnectedDevice; }
    bool isBluetoothConnected() const { return m_btConnected; }

private:
    AudioManager();
    ~AudioManager();

    void teardownSDPlayer();
    void teardownBluetoothSink();
    bool initSDPlayer();
    bool initBluetoothSink();

    OperationalMode m_currentMode;
    uint8_t m_currentVolume;
    int m_currentTrackIndex;
    bool m_isPaused;
    bool m_isMuted;

    // Separate pointers allocated dynamically to guarantee mutual exclusion in RAM
    Audio* m_sdAudio;
    BluetoothA2DPSink* m_a2dpSink;

    bool m_btConnected;
    String m_btConnectedDevice;
};
