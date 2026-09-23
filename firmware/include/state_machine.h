#pragma once
#include <Arduino.h>

enum class SystemState {
    OFF = 0,
    LOCAL_SD_STARTING = 1,
    LOCAL_SD_ACTIVE = 2,
    LOCAL_SD_STOPPING = 3,
    BT_STARTING = 4,
    BT_ACTIVE = 5,
    BT_STOPPING = 6,
    ERROR = 7
};

inline const char* stateToString(SystemState state) {
    switch (state) {
        case SystemState::OFF:                return "OFF (STANDBY)";
        case SystemState::LOCAL_SD_STARTING:  return "LOCAL_SD_STARTING";
        case SystemState::LOCAL_SD_ACTIVE:    return "LOCAL_SD_ACTIVE";
        case SystemState::LOCAL_SD_STOPPING:  return "LOCAL_SD_STOPPING";
        case SystemState::BT_STARTING:        return "BT_STARTING";
        case SystemState::BT_ACTIVE:          return "BT_ACTIVE";
        case SystemState::BT_STOPPING:        return "BT_STOPPING";
        case SystemState::ERROR:              return "ERROR";
        default:                              return "UNKNOWN";
    }
}
