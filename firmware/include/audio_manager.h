#pragma once
#include <Arduino.h>
#include "config.h"
#include "state_machine.h"
#include "bluetooth_audio.h"

class Audio; // Forward declare ESP32-audioI2S Audio class

struct MemorySnapshot {
    size_t internalHeapFree;
    size_t psramFree;
};

class AudioManager {
public:
    static AudioManager& instance() {
        static AudioManager inst;
        return inst;
    }

    void begin();
    void loop();

    // State Machine & Transition Management
    bool transitionTo(SystemState targetState);
    SystemState getState() const { return m_state; }

    // Deterministic Hardware Test Path (No SD or decoder required)
    bool playHardwareTone(uint16_t freqHz = 440, uint32_t durationMs = 1500);

    // Standalone SD Playback Controls
    bool playSDTrack(int trackIndex);
    void pauseSD();
    void resumeSD();
    void togglePlayPause();
    void stopSD();
    void nextTrack();
    void previousTrack();
    bool isPlaying() const;

    // Volume Control with Hard Ceiling (<= 65%)
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

    // Memory Accounting & Diagnostics
    MemorySnapshot getMemorySnapshot() const;
    void logMemoryDelta(const char* tag, const MemorySnapshot& before, const MemorySnapshot& after);

private:
    AudioManager();
    ~AudioManager();

    // Lifecycle encapsulation: Allocates and destroys decoder dynamically
    bool createSDDecoder();
    void destroySDDecoder();

    SystemState m_state;
    uint8_t m_currentVolume;
    int m_currentTrackIndex;
    bool m_isPaused;
    bool m_isMuted;

    // Dynamically managed decoder instance - NEVER global or static
    Audio* m_sdAudio;

    // Capability-gated Bluetooth Audio provider
    IBluetoothAudio* m_btAudio;

    MemorySnapshot m_baselineMemory;
};
