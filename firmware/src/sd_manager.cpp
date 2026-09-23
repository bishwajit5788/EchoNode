#include "sd_manager.h"
#include "tca9554.h"

SDManager::SDManager()
    : m_spi(nullptr),
      m_initialized(false),
      m_mounted(false) {}

bool SDManager::sd_init() {
    if (m_initialized) return true;

    Serial.println("[SD] Initializing SPI bus (SCK=14, MISO=16, MOSI=17)...");
    if (!m_spi) {
        m_spi = new SPIClass(FSPI);
        m_spi->begin(SD_SCK_PIN, SD_MISO_PIN, SD_MOSI_PIN, -1);
    }

    // Ensure TCA9554 IO Expander is ready
    if (!TCA9554::instance().isConnected()) {
        Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
        TCA9554::instance().begin(TCA9554_I2C_ADDR, Wire);
    }

    // Start with SD CS deselected (HIGH)
    TCA9554::instance().setSDCardCS(false);

    m_initialized = true;
    return true;
}

bool SDManager::sd_mount() {
    if (m_mounted) return true;
    if (!m_initialized) {
        if (!sd_init()) return false;
    }

    Serial.println("[SD] Asserting EXIO3 SD CS LOW and mounting FAT32 filesystem...");
    // Assert CS LOW via TCA9554
    TCA9554::instance().setSDCardCS(true);
    delay(10);

    // Pass SS as -1 since hardware CS is handled through TCA9554 EXIO3
    if (!SD.begin(-1, *m_spi, 20000000, "/sd", 5)) {
        Serial.println("[SD] ERROR: Card Mount Failed! Verify FAT32 formatting and <= 32GB capacity.");
        TCA9554::instance().setSDCardCS(false);
        m_mounted = false;
        return false;
    }

    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println("[SD] ERROR: No card detected.");
        TCA9554::instance().setSDCardCS(false);
        m_mounted = false;
        return false;
    }

    uint64_t totalMB = SD.cardSize() / (1024 * 1024);
    Serial.printf("[SD] Card Type: %d, Capacity: %llu MB\n", cardType, totalMB);

    if (totalMB > 32768) {
        Serial.println("[SD] ⚠️ WARNING: Card exceeds 32GB constraint in PDR. Ensure FAT32 clusters.");
    }

    m_mounted = true;
    sd_list_tracks();
    return true;
}

void SDManager::sd_unmount() {
    if (!m_mounted) return;
    Serial.println("[SD] Safely unmounting filesystem and releasing EXIO3 CS...");
    SD.end();
    TCA9554::instance().setSDCardCS(false); // Deassert CS (HIGH)
    m_mounted = false;
    m_tracks.clear();
}

std::vector<String> SDManager::sd_list_tracks() {
    m_tracks.clear();
    if (!m_mounted) return m_tracks;

    File root = SD.open("/");
    if (!root || !root.isDirectory()) {
        Serial.println("[SD] Failed to open root directory.");
        return m_tracks;
    }

    File file = root.openNextFile();
    while (file) {
        if (!file.isDirectory()) {
            String name = String(file.name());
            String lower = name;
            lower.toLowerCase();
            // Accept audio containers compatible with ESP32-audioI2S
            if (lower.endsWith(".m4a") || lower.endsWith(".mp3") || lower.endsWith(".aac") || lower.endsWith(".wav")) {
                m_tracks.push_back(name);
                Serial.printf("[SD] Track [%d]: %s (%u bytes)\n", (int)m_tracks.size(), name.c_str(), file.size());
            }
        }
        file = root.openNextFile();
    }
    root.close();
    Serial.printf("[SD] Total valid tracks discovered: %d\n", (int)m_tracks.size());
    return m_tracks;
}

float SDManager::sd_read_test(size_t test_bytes) {
    if (!m_mounted || m_tracks.empty()) return 0.0f;

    String samplePath = getTrackPath(0);
    File f = SD.open(samplePath.c_str(), FILE_READ);
    if (!f) return 0.0f;

    uint8_t buffer[512];
    size_t bytesRead = 0;
    unsigned long t0 = millis();

    while (f.available() && bytesRead < test_bytes) {
        size_t chunk = min((size_t)sizeof(buffer), test_bytes - bytesRead);
        int r = f.read(buffer, chunk);
        if (r <= 0) break;
        bytesRead += r;
    }
    unsigned long elapsed = millis() - t0;
    f.close();

    if (elapsed == 0) elapsed = 1;
    float kbps = ((float)bytesRead / (float)elapsed); // bytes/ms = KB/s
    Serial.printf("[SD] Benchmark: Read %u bytes in %lu ms (%.2f KB/s = %.2f MB/s)\n",
                  bytesRead, elapsed, kbps, kbps / 1024.0f);
    return kbps;
}

SDHealthInfo SDManager::sd_health() {
    SDHealthInfo info = {};
    info.mounted = m_mounted;
    if (m_mounted) {
        info.cardType = SD.cardType();
        info.totalSizeMB = SD.cardSize() / (1024 * 1024);
        info.usedBytesMB = SD.usedBytes() / (1024 * 1024);
        info.capacityCompliant = (info.totalSizeMB <= 32768);
        info.trackCount = (int)m_tracks.size();
        info.readSpeedKBps = sd_read_test(64 * 1024);
    }
    return info;
}

void SDManager::sd_shutdown() {
    sd_unmount();
    if (m_spi) {
        m_spi->end();
        delete m_spi;
        m_spi = nullptr;
    }
    m_initialized = false;
    Serial.println("[SD] Subsystem completely shutdown.");
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
