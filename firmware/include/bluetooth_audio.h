#pragma once
#include <Arduino.h>

enum class BluetoothAudioStatus {
    NOT_SUPPORTED = 0,    // ESP32-S3 lacks Classic Bluetooth (BR/EDR)
    IDLE = 1,
    DISCOVERING = 2,
    CONNECTED = 3,
    ERROR = 4
};

class IBluetoothAudio {
public:
    virtual ~IBluetoothAudio() = default;

    virtual bool isSupported() const = 0;
    virtual BluetoothAudioStatus getStatus() const = 0;
    virtual const char* getHardwareExplanation() const = 0;

    virtual bool start() = 0;
    virtual void stop() = 0;
    virtual bool isConnected() const = 0;
    virtual String getConnectedDeviceName() const = 0;
};

class ESP32S3BluetoothAudio : public IBluetoothAudio {
public:
    static ESP32S3BluetoothAudio& instance() {
        static ESP32S3BluetoothAudio inst;
        return inst;
    }

    bool isSupported() const override { return false; }
    BluetoothAudioStatus getStatus() const override { return BluetoothAudioStatus::NOT_SUPPORTED; }
    const char* getHardwareExplanation() const override {
        return "ESP32-S3 SoC lacks Classic Bluetooth (BR/EDR) hardware required for A2DP Sink audio streaming.";
    }

    bool start() override;
    void stop() override;
    bool isConnected() const override { return false; }
    String getConnectedDeviceName() const override { return ""; }

private:
    ESP32S3BluetoothAudio() = default;
};
