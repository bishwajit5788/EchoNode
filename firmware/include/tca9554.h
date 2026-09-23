#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "config.h"

// TCA9554 8-bit I2C I/O Expander Register Map
#define TCA9554_REG_INPUT     0x00
#define TCA9554_REG_OUTPUT    0x01
#define TCA9554_REG_POLARITY  0x02
#define TCA9554_REG_CONFIG    0x03

class TCA9554 {
public:
    static TCA9554& instance() {
        static TCA9554 inst;
        return inst;
    }

    bool begin(uint8_t address = TCA9554_I2C_ADDR, TwoWire& wire = Wire);
    bool isConnected() const { return m_initialized; }

    bool pinModeEX(uint8_t pin, uint8_t mode);
    bool digitalWriteEX(uint8_t pin, uint8_t val);
    int digitalReadEX(uint8_t pin);

    // Dedicated MicroSD CS Control on EXIO3
    void setSDCardCS(bool active);

private:
    TCA9554();
    bool writeReg(uint8_t reg, uint8_t val);
    uint8_t readReg(uint8_t reg);

    uint8_t m_address;
    TwoWire* m_wire;
    uint8_t m_outputCache;
    uint8_t m_configCache;
    bool m_initialized;
};
