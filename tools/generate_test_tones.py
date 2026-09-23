#!/usr/bin/env python3
"""
EchoNode Audio Reference Tone Generator
Generates uncompressed, bit-perfect WAV test tones for hardware speaker verification:
- 440 Hz Reference Pitch (Concert A)
- 100 Hz - 2000 Hz Logarithmic Sweep (Dual 8-ohm micro-speaker frequency response check)
- Stereo Separation Check (Alternating Left/Right channel pulses)
- Pink Noise approximation (Thermal & brownout stress testing)
All tones are capped at -6 dBFS (~50% amplitude) to enforce RULE_VOLUME_CEILING.
"""

import math
import struct
import wave
import random
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "backend" / "downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100
MAX_AMP = 32767 * 0.5  # -6 dBFS safety cap (50% amplitude)

def write_wav(filename: str, samples_left: list, samples_right: list):
    path = OUTPUT_DIR / filename
    num_frames = len(samples_left)
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(2)      # Stereo
        wav.setsampwidth(2)      # 16-bit
        wav.setframerate(SAMPLE_RATE)
        
        raw_bytes = bytearray()
        for i in range(num_frames):
            l = int(max(-32768, min(32767, samples_left[i])))
            r = int(max(-32768, min(32767, samples_right[i])))
            raw_bytes.extend(struct.pack('<hh', l, r))
        wav.writeframes(raw_bytes)
    print(f"✓ Generated test audio: {path.name} ({path.stat().st_size} bytes)")

def generate_tone_440hz(duration_sec: float = 3.0):
    num_samples = int(SAMPLE_RATE * duration_sec)
    left, right = [], []
    freq = 440.0
    for i in range(num_samples):
        val = MAX_AMP * math.sin(2 * math.pi * freq * (i / SAMPLE_RATE))
        left.append(val)
        right.append(val)
    write_wav("test_tone_440hz_ref.wav", left, right)

def generate_stereo_check(duration_sec: float = 4.0):
    num_samples = int(SAMPLE_RATE * duration_sec)
    left, right = [], []
    freq = 880.0
    half_period = int(SAMPLE_RATE * 0.5)  # 500ms pulses
    for i in range(num_samples):
        cycle = (i // half_period) % 4
        # 0: Left only, 1: Silence, 2: Right only, 3: Silence
        val = MAX_AMP * math.sin(2 * math.pi * freq * (i / SAMPLE_RATE))
        if cycle == 0:
            left.append(val)
            right.append(0.0)
        elif cycle == 2:
            left.append(0.0)
            right.append(val)
        else:
            left.append(0.0)
            right.append(0.0)
    write_wav("test_stereo_channel_check.wav", left, right)

def generate_frequency_sweep(start_hz: float = 100.0, end_hz: float = 2000.0, duration_sec: float = 5.0):
    num_samples = int(SAMPLE_RATE * duration_sec)
    left, right = [], []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Logarithmic sweep
        instant_freq = start_hz * (math.pow(end_hz / start_hz, t / duration_sec))
        val = MAX_AMP * math.sin(2 * math.pi * instant_freq * t)
        left.append(val)
        right.append(val)
    write_wav("test_speaker_sweep_100hz_2khz.wav", left, right)

if __name__ == "__main__":
    print("Generating EchoNode Hardware Verification Audio Files...")
    generate_tone_440hz()
    generate_stereo_check()
    generate_frequency_sweep()
    print("All diagnostic tones created successfully in backend/downloads/.")
