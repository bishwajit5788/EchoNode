import sys
import struct
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.extractor import validate_youtube_url, inspect_mp4_container_tracks

def test_url_validation():
    valid_urls = [
        "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
        "https://youtu.be/aqz-KE-bpKQ",
        "http://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://music.youtube.com/watch?v=abcdef12345",
    ]
    invalid_urls = [
        "https://malicious-site.com/video.mp4",
        "ftp://youtube.com/file",
        "https://www.youtube.com/watch?v=123;rm -rf /",
        "https://www.youtube.com/watch?v=123&test=1`touch pwn`",
        "not-a-url",
        "javascript:alert(1)",
    ]

    for u in valid_urls:
        assert validate_youtube_url(u), f"Expected valid: {u}"
        print(f"✓ Valid URL: {u}")

    for u in invalid_urls:
        assert not validate_youtube_url(u), f"Expected invalid: {u}"
        print(f"✓ Correctly rejected: {u}")

def test_audio_only_inspection():
    downloads_dir = backend_dir / "downloads"
    m4a_files = list(downloads_dir.glob("*.m4a"))
    if m4a_files:
        test_file = m4a_files[0]
        audio_cnt, video_cnt = inspect_mp4_container_tracks(test_file)
        print(f"Inspecting {test_file.name}: Audio tracks: {audio_cnt}, Video tracks: {video_cnt}")
        assert audio_cnt >= 1, "Expected at least 1 audio track"
        assert video_cnt == 0, f"Expected 0 video tracks, found {video_cnt}!"
        print("✓ Verified real M4A file contains PURE AUDIO (0 video streams)")

def test_synthetic_video_stream_rejection(tmp_path: Path):
    # Construct a synthetic mock MP4 with a 'vide' handler atom
    mock_file = tmp_path / "mock_video.m4a"
    
    # Simple atom builder: [size(4)][type(4)][data]
    def make_atom(atom_type: bytes, payload: bytes) -> bytes:
        size = 8 + len(payload)
        return struct.pack(">I", size) + atom_type + payload

    # hdlr atom with 'vide' handler type
    hdlr_payload = b"\x00\x00\x00\x00" + b"\x00\x00\x00\x00" + b"vide" + b"VideoHandler\x00"
    hdlr_atom = make_atom(b"hdlr", hdlr_payload)
    trak_atom = make_atom(b"trak", hdlr_atom)
    moov_atom = make_atom(b"moov", trak_atom)

    with open(mock_file, "wb") as f:
        f.write(make_atom(b"ftyp", b"M4A \x00\x00\x02\x00isomiso2"))
        f.write(moov_atom)

    audio_cnt, video_cnt = inspect_mp4_container_tracks(mock_file)
    print(f"Synthetic Video Test: Audio={audio_cnt}, Video={video_cnt}")
    assert video_cnt > 0, "Failed to detect synthetic video track!"
    print("✓ Successfully detected and flagged video stream in synthetic container")
    mock_file.unlink(missing_ok=True)

if __name__ == "__main__":
    import tempfile
    print("Running Audio-Only & URL Hardening Verification...")
    test_url_validation()
    test_audio_only_inspection()
    with tempfile.TemporaryDirectory() as td:
        test_synthetic_video_stream_rejection(Path(td))
    print("All backend security and audio-only tests PASSED!")
