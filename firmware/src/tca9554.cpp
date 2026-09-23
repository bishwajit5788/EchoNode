#include "tca9554.h"

TCA9554::TCA9554()
    : m_address(TCA9554_I2C_ADDR),
      m_wire(&Wire),
      m_outputCache(0xFF),
      m_configCache(0xFF),
      m_initialized(false) {}

bool TCA9554::writeReg(uint8_t reg, uint8_t val) {
    if (!m_wire) return false;
    m_wire->beginTransmission(m_address);
    m_wire->write(reg);
    m_wire->write(val);
    return (m_wire->endTransmission() == 0);
}

uint8_t TCA9554::readReg(uint8_t reg) {
    if (!m_wire) return 0;
    m_wire->beginTransmission(m_address);
    m_wire->write(reg);
    if (m_wire->endTransmission() != 0) return 0;
    if (m_wire->requestFrom(m_address, (uint8_t)1) == 1) {
        return m_wire->read();
    }
    return 0;
}

bool TCA9554::begin(uint8_t address, TwoWire& wire) {
    m_address = address;
    m_wire = &wire;

    // Test communication
    m_wire->beginTransmission(m_address);
    if (m_wire->endTransmission() != 0) {
        Serial.printf("[TCA9554] Failed to connect to IO expander at 0x%02X\n", m_address);
        m_initialized = false;
        return false;
    }

    // Read current config and output states
    m_configCache = readReg(TCA9554_REG_CONFIG);
    m_outputCache = readReg(TCA9554_REG_OUTPUT);

    // Ensure EXIO3 (MicroSD CS) is configured as OUTPUT and set HIGH (inactive)
    pinModeEX(TCA9554_EXIO3, OUTPUT);
    digitalWriteEX(TCA9554_EXIO3, HIGH);

    m_initialized = true;
    Serial.printf("[TCA9554] Initialized at 0x%02X (EXIO3 SD CS set HIGH)\n", m_address);
    return true;
}

bool TCA9554::pinModeEX(uint8_t pin, uint8_t mode) {
    if (pin > 7) return false;
    if (mode == OUTPUT) {
        m_configCache &= ~(1 << pin); // 0 = Output
    } else {
        m_configCache |= (1 << pin);  // 1 = Input
    }
    return writeReg(TCA9554_REG_CONFIG, m_configCache);
}

bool TCA9554::digitalWriteEX(uint8_t pin, uint8_t val) {
    if (pin > 7) return false;
    if (val) {
        m_outputCache |= (1 << pin);
    } else {
        m_outputCache &= ~(1 << pin);
    }
    return writeReg(TCA9554_REG_OUTPUT, m_outputCache);
}

int TCA9554::digitalReadEX(uint8_t pin) {
    if (pin > 7) return LOW;
    uint8_t input = readReg(TCA9554_REG_INPUT);
    return (input & (1 << pin)) ? HIGH : LOW;
}

void TCA9554::setSDCardCS(bool active) {
    // MicroSD CS is active LOW
    // active = true -> drive EXIO3 LOW (selected)
    // active = false -> drive EXIO3 HIGH (deselected)
    digitalWriteEX(TCA9554_EXIO3, active ? LOW : HIGH);
}
