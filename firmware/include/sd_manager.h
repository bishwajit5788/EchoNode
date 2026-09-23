#pragma once
#include <Arduino.h>
#include <FS.h>
#include <SD.h>
#include <SPI.h>
#include <vector>
#include "config.h"

struct SDHealthInfo {
    bool mounted;
    uint8_t cardType;
    uint64_t totalSizeMB;
    uint64_t usedBytesMB;
    float readSpeedKBps;
    int trackCount;
    bool capacityCompliant; // <= 32GB
};

class SDManager {
public:
    static SDManager& instance() {
        static SDManager inst;
        return inst;
    }

    bool sd_init();
    bool sd_mount();
    void sd_unmount();
    std::vector<String> sd_list_tracks();
    float sd_read_test(size_t test_bytes = 128 * 1024);
    SDHealthInfo sd_health();
    void sd_shutdown();

    bool isMounted() const { return m_mounted; }
    int getTrackCount() const { return (int)m_tracks.size(); }
    String getTrackPath(int index) const;
    String getTrackTitle(int index) const;

private:
    SDManager();
    SPIClass* m_spi;
    bool m_initialized;
    bool m_mounted;
    std::vector<String> m_tracks;
};
