#pragma once
#include <Arduino.h>
#include <FS.h>
#include <SD.h>
#include <SPI.h>
#include <vector>
#include "config.h"

class SDManager {
public:
    static SDManager& instance() {
        static SDManager inst;
        return inst;
    }

    bool mount();
    void unmount();
    bool isMounted() const { return m_mounted; }

    int scanTracks();
    int getTrackCount() const { return (int)m_tracks.size(); }
    String getTrackPath(int index) const;
    String getTrackTitle(int index) const;

private:
    SDManager();
    SPIClass* m_spi;
    bool m_mounted;
    std::vector<String> m_tracks;
};
