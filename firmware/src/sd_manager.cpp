#include "sd_manager.h"

SDManager::SDManager() : m_spi(nullptr), m_mounted(false) {}

bool SDManager::mount() {
    if (m_mounted) return true;

    Serial.println("[SD] Initializing SPI bus for MicroSD...");
    if (!m_spi) {
        m_spi = new SPIClass(FSPI);
        m_spi->begin(SD_SCK_PIN, SD_MISO_PIN, SD_MOSI_PIN, SD_CS_PIN);
    }

    if (!SD.begin(SD_CS_PIN, *m_spi, 20000000)) {
        Serial.println("[SD] ERROR: Card Mount Failed. Verify FAT32 format and <=32GB capacity.");
        m_mounted = false;
        return false;
    }

    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println("[SD] ERROR: No MicroSD card attached");
        m_mounted = false;
        return false;
    }

    uint64_t cardSizeMB = SD.cardSize() / (1024 * 1024);
    Serial.printf("[SD] Card Type: %d, Size: %llu MB\n", cardType, cardSizeMB);
    if (cardSizeMB > 32768) {
        Serial.println("[SD] WARNING: Card size exceeds 32GB constraint in PDR. Ensure FAT32 cluster formatting.");
    }

    m_mounted = true;
    scanTracks();
    return true;
}

void SDManager::unmount() {
    if (!m_mounted) return;
    Serial.println("[SD] Safely unmounting MicroSD storage to release SPI bus (RULE_MUTUAL_EXCLUSION)...");
    SD.end();
    m_mounted = false;
    m_tracks.clear();
}

int SDManager::scanTracks() {
    m_tracks.clear();
    if (!m_mounted) return 0;

    File root = SD.open("/");
    if (!root || !root.isDirectory()) {
        Serial.println("[SD] Failed to open root directory");
        return 0;
    }

    File file = root.openNextFile();
    while (file) {
        if (!file.isDirectory()) {
            String name = String(file.name());
            String lower = name;
            lower.toLowerCase();
            // Filter strictly for audio files extracted by backend or stored on card
            if (lower.endsWith(".m4a") || lower.endsWith(".mp3") || lower.endsWith(".aac")) {
                m_tracks.push_back(name);
                Serial.printf("[SD] Found Track [%d]: %s (%u bytes)\n", (int)m_tracks.size(), name.c_str(), file.size());
            }
        }
        file = root.openNextFile();
    }

    Serial.printf("[SD] Scan complete. Total valid tracks: %d\n", (int)m_tracks.size());
    return (int)m_tracks.size();
}

String SDManager::getTrackPath(int index) const {
    if (index >= 0 && index < (int)m_tracks.size()) {
        String path = m_tracks[index];
        if (!path.startsWith("/")) path = "/" + path;
        return path;
    }
    return "";
}

String SDManager::getTrackTitle(int index) const {
    if (index >= 0 && index < (int)m_tracks.size()) {
        String filename = m_tracks[index];
        if (filename.startsWith("/")) filename = filename.substring(1);
        int dot = filename.lastIndexOf('.');
        if (dot > 0) filename = filename.substring(0, dot);
        filename.replace("_", " ");
        return filename;
    }
    return "No Track";
}
