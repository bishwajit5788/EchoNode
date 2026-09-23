#!/usr/bin/env python3
"""
EchoNode Partition Table Validator
Audits partitions_16MB.csv for:
- 4KB sector alignment on all partition offsets and sizes
- 64KB alignment for OTA app partitions (app0, app1)
- Overlapping partition boundaries
- Total allocated size within 16MB (0x1000000 bytes)
- Flash bootloader & partition table reserved regions
"""

import sys
import re
from pathlib import Path

FLASH_TOTAL_SIZE = 16 * 1024 * 1024  # 16 MB (0x1000000)
SECTOR_SIZE = 4096                   # 4 KB (0x1000)
OTA_APP_ALIGNMENT = 65536            # 64 KB (0x10000)
BOOTLOADER_END = 0x8000              # 32 KB reserved for bootloader
PARTITION_TABLE_END = 0x9000         # 4 KB reserved for partition table

def parse_size(val: str) -> int:
    val = val.strip()
    if val.startswith("0x") or val.startswith("0X"):
        return int(val, 16)
    if val.endswith("K") or val.endswith("k"):
        return int(val[:-1]) * 1024
    if val.endswith("M") or val.endswith("m"):
        return int(val[:-1]) * 1024 * 1024
    return int(val)

def validate_partitions_csv(csv_path: Path):
    print("=" * 60)
    print(f"Auditing Partition Table: {csv_path.name}")
    print("=" * 60)

    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        return False

    partitions = []
    with open(csv_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 5:
                print(f"❌ Line {line_num}: Insufficient columns: '{line}'")
                return False
            name, ptype, psubtype, offset_str, size_str = parts[:5]
            flags = parts[5].strip() if len(parts) > 5 else ""

            offset = parse_size(offset_str)
            size = parse_size(size_str)
            partitions.append({
                "line": line_num,
                "name": name,
                "type": ptype,
                "subtype": psubtype,
                "offset": offset,
                "size": size,
                "flags": flags
            })

    # Sort partitions by offset
    partitions.sort(key=lambda p: p["offset"])

    errors = []
    warnings = []

    last_end = PARTITION_TABLE_END

    for p in partitions:
        name = p["name"]
        offset = p["offset"]
        size = p["size"]
        end = offset + size

        # Check reserved bootloader/partition-table range
        if offset < PARTITION_TABLE_END:
            errors.append(f"Partition '{name}' starts at 0x{offset:X} which collides with reserved bootloader/partition table (ends at 0x{PARTITION_TABLE_END:X}).")

        # Check 4KB sector alignment
        if offset % SECTOR_SIZE != 0:
            errors.append(f"Partition '{name}' offset 0x{offset:X} is not aligned to 4KB sector (0x{SECTOR_SIZE:X}).")
        if size % SECTOR_SIZE != 0:
            errors.append(f"Partition '{name}' size 0x{size:X} ({size} bytes) is not a multiple of 4KB sectors.")

        # Check 64KB alignment for OTA app partitions
        if p["type"] == "app" and offset % OTA_APP_ALIGNMENT != 0:
            errors.append(f"App partition '{name}' offset 0x{offset:X} is not 64KB aligned (0x{OTA_APP_ALIGNMENT:X}). Required for ESP32 MMU.")

        # Check overlap
        if offset < last_end:
            errors.append(f"Partition '{name}' offset 0x{offset:X} overlaps with previous partition ending at 0x{last_end:X}.")

        # Check total flash bound
        if end > FLASH_TOTAL_SIZE:
            errors.append(f"Partition '{name}' extends to 0x{end:X} which exceeds 16MB flash capacity (0x{FLASH_TOTAL_SIZE:X}).")

        print(f"  [{p['name']:<10}] Type: {p['type']:<5} Subtype: {p['subtype']:<8} "
              f"Offset: 0x{offset:06X} -> 0x{end:06X} ({size / (1024*1024):.2f} MB)")

        last_end = max(last_end, end)

    print("-" * 60)
    print(f"Total Flash Allocated: {last_end / (1024*1024):.2f} MB / {FLASH_TOTAL_SIZE / (1024*1024):.2f} MB ({(last_end / FLASH_TOTAL_SIZE)*100:.1f}%)")

    if errors:
        print("\n❌ VALIDATION FAILED with errors:")
        for e in errors:
            print(f"  - {e}")
        return False

    print("\n✓ Partition table is 100% compliant with ESP32-S3 16MB flash & MMU alignment rules!")
    return True

if __name__ == "__main__":
    csv_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "firmware" / "partitions_16MB.csv"
    success = validate_partitions_csv(csv_file)
    sys.exit(0 if success else 1)
