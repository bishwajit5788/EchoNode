import os
import sys
import asyncio
from pathlib import Path
import unittest

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import sanitize_fat32_filename, settings
from app.services.extractor import AudioExtractor, validate_youtube_url, extractor_service
from app.services.job_store import job_store
from app.models import ExtractionRequest, JobStatus
from app.api.routes import (
    submit_extraction,
    get_job_status,
    get_all_jobs,
    list_audio_files,
    download_file,
    system_info
)
from fastapi import HTTPException

class TestBackendRoutes(unittest.TestCase):
    def setUp(self):
        job_store.clear()

    def test_sanitize_fat32_filename(self):
        cases = [
            ("Normal Song Title", "Normal_Song_Title"),
            ("Song / with : illegal * chars? <here>", "Song_with_illegal_chars_here"),
            ("Song 🎵 With Emojis & Symbols!", "Song_With_Emojis_&_Symbols!"),
            ("...Leading and Trailing Dots...", "Leading_and_Trailing_Dots"),
            ("A" * 100, "A" * 60),  # Max length clamp
        ]
        for inp, expected in cases:
            out = sanitize_fat32_filename(inp)
            self.assertLessEqual(len(out), 60)
            self.assertFalse(any(c in out for c in r'/\:*?"<>|'))

    def test_validate_youtube_url(self):
        # Valid URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=xvT1jH8B9AM",
            "https://youtube.com/watch?v=xvT1jH8B9AM",
            "https://youtu.be/xvT1jH8B9AM",
            "https://m.youtube.com/watch?v=xvT1jH8B9AM",
            "https://music.youtube.com/watch?v=xvT1jH8B9AM",
        ]
        for u in valid_urls:
            self.assertTrue(validate_youtube_url(u), f"Should be valid: {u}")

        # Invalid / Malicious URLs
        invalid_urls = [
            "https://evil.com/video.mp4",
            "http://notyoutube.com",
            "https://youtube.com.attacker.com/watch",
            "https://youtube.com/watch?v=123; rm -rf /",
            "https://youtube.com/watch?v=123&test=1",  # Command char rejection
            "ftp://youtube.com/test",
            "not a url",
            "",
        ]
        for u in invalid_urls:
            self.assertFalse(validate_youtube_url(u), f"Should be invalid: {u}")

    def test_system_info_endpoint(self):
        res = asyncio.run(system_info())
        self.assertIn("app", res)
        self.assertIn("version", res)
        self.assertIn("ffmpeg_available", res)
        self.assertIn("sd_format_standard", res)

    def test_submit_extraction_invalid_url_rejected(self):
        req = ExtractionRequest(url="https://attacker.com/malicious.mp3")
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(submit_extraction(req))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Invalid or unsupported URL", ctx.exception.detail)

    def test_submit_extraction_valid_url_queues_job(self):
        req = ExtractionRequest(url="https://www.youtube.com/watch?v=xvT1jH8B9AM")
        
        async def mock_start(url, format_pref="m4a", custom_title=None, wait_for_completion=False):
            import time
            job = JobStatus(job_id="mock-job-123", url=url, status="queued", progress=0.0, created_at=time.time())
            job_store.create_job(job)
            return "mock-job-123"

        orig_start = extractor_service.start_extraction_job
        extractor_service.start_extraction_job = mock_start
        try:
            resp = asyncio.run(submit_extraction(req))
            self.assertEqual(resp.job_id, "mock-job-123")
            self.assertEqual(resp.status, "queued")

            # Verify job is tracked in store
            job = asyncio.run(get_job_status(resp.job_id))
            self.assertEqual(job.job_id, "mock-job-123")
        finally:
            extractor_service.start_extraction_job = orig_start

    def test_get_nonexistent_job_returns_404(self):
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(get_job_status("nonexistent-id-999"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_download_nonexistent_file_returns_404(self):
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(download_file("does_not_exist_xyz.m4a"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_extractor_options(self):
        extractor = AudioExtractor()
        self.assertTrue(extractor.downloads_dir.exists())
        self.assertIsInstance(extractor.has_ffmpeg, bool)

if __name__ == "__main__":
    unittest.main()
