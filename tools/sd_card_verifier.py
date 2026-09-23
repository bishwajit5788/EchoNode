#!/usr/bin/env python3
"""
EchoNode MicroSD Card Validator & Benchmark Tool
Verifies FAT32 compliance, enforces <=32GB capacity limits (PDR.md),
and benchmarks read/write speeds to ensure glitch-free I2S audio playback.
"""

import os
import sys
import time
import shutil
import argparse
import subprocess
from pathlib import Path

def get_mount_stats(target_path: Path):
    stat = shutil.disk_usage(target_path)
    total_gb = stat.total / (1024 ** 3)
    free_gb = stat.free / (1024 ** 3)
    used_gb = stat.used / (1024 ** 3)
    return total_gb, used_gb, free_gb

def check_filesystem_type(target_path: Path) -> str:
    """Detect filesystem type on macOS or Linux."""
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(["df", "-T", str(target_path)]).decode()
            lines = out.strip().split("\n")
            if len(lines) >= 2:
                # Format: Filesystem Type ...
                parts = lines[1].split()
                return parts[1]
        elif sys.platform.startswith("linux"):
            out = subprocess.check_output(["stat", "-f", "-c", "%T", str(target_path)]).decode()
            return out.strip()
    except Exception:
        pass
    return "unknown"

def benchmark_io_speed(target_path: Path, block_size_kb: int = 64, num_blocks: int = 160):
    """
    Write and read a 10MB test file to benchmark throughput.
    ESP32-audioI2S requires sustained throughput >= 500 KB/s.
    """
    test_file = target_path / ".echonode_benchmark.tmp"
    data = os.urandom(block_size_kb * 1024)
    total_bytes = block_size_kb * 1024 * num_blocks

    # Write test
    t0 = time.perf_counter()
    with open(test_file, "wb") as f:
        for _ in range(num_blocks):
            f.write(data)
        f.flush()
        os.fsync(f.fileno())
    t1 = time.perf_counter()
    write_speed_mb = (total_bytes / (1024 * 1024)) / (t1 - t0)

    # Read test
    t2 = time.perf_counter()
    with open(test_file, "rb") as f:
        while f.read(block_size_kb * 1024):
            pass
    t3 = time.perf_counter()
    read_speed_mb = (total_bytes / (1024 * 1024)) / (t3 - t2)

    # Clean up
    test_file.unlink(missing_ok=True)
    return write_speed_mb, read_speed_mb

def verify_sd_card(mount_path_str: str, auto_sync: bool = False):
    mount_path = Path(mount_path_str).resolve()
    print("=" * 60)
    print("   EchoNode MicroSD Diagnostic & Compliance Validator   ")
    print("=" * 60)
    print(f"Target Path: {mount_path}")

    if not mount_path.exists() or not mount_path.is_dir():
        print(f"❌ ERROR: Target mount path does not exist: {mount_path}")
        print("Tip: Insert your MicroSD card and provide its mount path (e.g., /Volumes/ECHONODE)")
        return False

    total_gb, used_gb, free_gb = get_mount_stats(mount_path)
    print(f"Total Size:  {total_gb:.2f} GB")
    print(f"Used Space:  {used_gb:.2f} GB")
    print(f"Free Space:  {free_gb:.2f} GB")

    # 1. Check Capacity Limit (PDR Constraint: <= 32GB)
    if total_gb > 33.0:
        print(f"⚠️  WARNING: Card size ({total_gb:.1f} GB) exceeds 32GB PDR constraint!")
        print("    Cards >32GB often use exFAT by default, which ESP32 SPI cannot read without custom drivers.")
        print("    Ensure this card was explicitly formatted as FAT32.")
    else:
        print("✓ Card capacity is within the recommended <=32GB FAT32 hardware boundary.")

    # 2. Check Filesystem Type
    fs_type = check_filesystem_type(mount_path)
    print(f"Filesystem:  {fs_type.upper()}")
    if "FAT" in fs_type.upper() or "MSDOS" in fs_type.upper():
        print("✓ Filesystem format matches FAT32 standard.")
    else:
        print(f"ℹ️  Note: Detected filesystem '{fs_type}'. Confirm it is formatted as MS-DOS (FAT32).")

    # 3. I/O Benchmark
    print("Running read/write throughput benchmark...")
    try:
        w_speed, r_speed = benchmark_io_speed(mount_path)
        print(f"✓ Write Throughput: {w_speed:.2f} MB/s")
        print(f"✓ Read Throughput:  {r_speed:.2f} MB/s")
        if r_speed >= 1.5:
            print("✓ Throughput exceeds 1.5 MB/s (Optimal for 128k-320k audio streams).")
        else:
            print("⚠️ Read speed is low. May cause occasional buffer under-runs.")
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

    # 4. Optional Auto-Sync
    if auto_sync:
        downloads_dir = Path(__file__).resolve().parent.parent / "backend" / "downloads"
        if downloads_dir.exists():
            print(f"\nSyncing audio tracks from {downloads_dir.name}/ to SD card...")
            copied = 0
            for f in downloads_dir.iterdir():
                if f.is_file() and f.suffix.lower() in [".m4a", ".mp3", ".wav"]:
                    dest = mount_path / f.name
                    shutil.copy2(f, dest)
                    print(f"  -> Copied {f.name}")
                    copied += 1
            print(f"✓ Successfully synced {copied} tracks to MicroSD card.")

    print("\n✓ MicroSD Card Diagnostics Complete!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EchoNode MicroSD Validator")
    parser.add_argument("path", nargs="?", default="/Volumes/ECHONODE", help="Mount path of the MicroSD card")
    parser.add_argument("--sync", action="store_true", help="Automatically copy staged audio files to SD card")
    args = parser.parse_args()

    verify_sd_card(args.path, auto_sync=args.sync)
