import os
import re
from pathlib import Path
from pydantic import BaseModel

# Base directory for EchoNode backend
BACKEND_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BACKEND_DIR / "downloads"
STATIC_DIR = BACKEND_DIR / "static"

# Ensure directories exist
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "EchoNode Ingestion Hub"
    version: str = "1.0.0"
    downloads_dir: Path = DOWNLOADS_DIR
    static_dir: Path = STATIC_DIR
    default_audio_format: str = "m4a"
    max_title_length: int = 60
    # Maximum recommended bitrates for ESP32-S3 I2S stream decoding (kbps)
    target_audio_bitrate_kbps: int = 128

settings = Settings()

def sanitize_fat32_filename(name: str, max_length: int = 60) -> str:
    """
    Sanitize string to guarantee safe compatibility with FAT32 MicroSD cards.
    Eliminates illegal characters: / \\ : * ? " < > | and non-ASCII or problematic control symbols.
    Limits base length to prevent path overflow on 8.3 / FAT32 systems.
    """
    # Replace illegal FAT32 characters with underscores
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Remove leading/trailing periods or spaces
    cleaned = cleaned.strip(". ")
    # Replace non-ascii characters with close ASCII or underscores
    cleaned = cleaned.encode("ascii", "ignore").decode("ascii")
    # Collapse multiple consecutive underscores or spaces
    cleaned = re.sub(r'[\s_]+', '_', cleaned)
    if not cleaned:
        cleaned = "audio_track"
    return cleaned[:max_length]
