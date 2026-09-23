import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import sanitize_fat32_filename, settings
from app.services.extractor import AudioExtractor

def test_sanitize_fat32_filename():
    cases = [
        ("Normal Song Title", "Normal_Song_Title"),
        ("Song / with : illegal * chars? <here>", "Song_with_illegal_chars_here"),
        ("Song 🎵 With Emojis & Symbols!", "Song_With_Emojis_&_Symbols!"),
        ("...Leading and Trailing Dots...", "Leading_and_Trailing_Dots"),
        ("A" * 100, "A" * 60),  # Max length clamp
    ]
    for inp, expected in cases:
        out = sanitize_fat32_filename(inp)
        assert len(out) <= 60, f"Exceeded length for {inp}: {len(out)}"
        assert not any(c in out for c in r'/\:*?"<>|'), f"Contains illegal char in {out}"
        print(f"✓ Sanitize: '{inp[:25]}...' -> '{out}'")

def test_extractor_options():
    extractor = AudioExtractor()
    assert extractor.downloads_dir.exists(), "Downloads directory does not exist"
    print(f"✓ Downloads directory verified: {extractor.downloads_dir}")
    print(f"✓ FFmpeg detected: {extractor.has_ffmpeg}")

if __name__ == "__main__":
    print("Running EchoNode Backend Diagnostics...")
    test_sanitize_fat32_filename()
    test_extractor_options()
    print("All unit tests passed successfully!")
