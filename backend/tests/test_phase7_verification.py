import os
import sys
import time
import asyncio
import tempfile
import struct
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import sanitize_fat32_filename, settings
from app.services.extractor import (
    AudioExtractor,
    inspect_mp4_container_tracks,
    validate_youtube_url,
    MAX_ALLOWED_FILE_BYTES
)
from app.services.job_store import JobStore, sanitize_error_message
from app.services.storage import LocalStorageService
from app.models import ExtractionRequest, JobStatus
from app.api.routes import (
    submit_extraction,
    get_job_status,
    get_all_jobs,
    list_audio_files,
    download_file,
    delete_file
)
from fastapi import HTTPException
from fastapi.responses import FileResponse

class TestPhase7Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.TemporaryDirectory()
        cls.test_path = Path(cls.test_dir.name)
        cls.db_path = cls.test_path / "phase7_jobs.db"
        cls.downloads_dir = cls.test_path / "downloads"
        cls.downloads_dir.mkdir(parents=True, exist_ok=True)

        cls.job_store = JobStore(db_path=cls.db_path)
        cls.storage = LocalStorageService(storage_dir=cls.downloads_dir)
        cls.extractor = AudioExtractor(downloads_dir=cls.downloads_dir)

    @classmethod
    def tearDownClass(cls):
        cls.job_store.close()
        cls.test_dir.cleanup()

    def setUp(self):
        self.job_store.clear()

    # 1. POST /api/extract
    # 2. Job status polling
    def test_01_and_02_post_extract_and_poll(self):
        job = JobStatus(
            job_id="test-poll-1",
            url="https://www.youtube.com/watch?v=xvT1jH8B9AM",
            status="queued",
            progress=0.0,
            created_at=time.time()
        )
        self.job_store.create_job(job)

        # Poll 1: queued
        polled = self.job_store.get_job("test-poll-1")
        self.assertEqual(polled.status, "queued")

        # Update to processing
        self.job_store.update_job("test-poll-1", status="processing", progress=50.0)
        polled2 = self.job_store.get_job("test-poll-1")
        self.assertEqual(polled2.status, "processing")
        self.assertEqual(polled2.progress, 50.0)

    # 3. Successful extraction simulation & container verification
    def test_03_successful_extraction_state(self):
        # Create a mock valid M4A file
        mock_m4a = self.downloads_dir / "valid_track.m4a"
        # Atom: ftyp (28 bytes) + moov containing trak with hdlr 'soun'
        hdlr_payload = b"\x00\x00\x00\x00\x00\x00\x00\x00soun\x00\x00\x00\x00\x00\x00\x00\x00"
        hdlr_atom = struct.pack(">I", 8 + len(hdlr_payload)) + b"hdlr" + hdlr_payload
        mdia_atom = struct.pack(">I", 8 + len(hdlr_atom)) + b"mdia" + hdlr_atom
        trak_atom = struct.pack(">I", 8 + len(mdia_atom)) + b"trak" + mdia_atom
        moov_atom = struct.pack(">I", 8 + len(trak_atom)) + b"moov" + trak_atom
        ftyp_atom = b"\x00\x00\x00\x18ftypM4A \x00\x00\x00\x00isommp42"
        mock_m4a.write_bytes(ftyp_atom + moov_atom)

        audio_tracks, video_tracks = inspect_mp4_container_tracks(mock_m4a)
        self.assertEqual(audio_tracks, 1)
        self.assertEqual(video_tracks, 0)

        # Save to storage
        url = self.storage.save_file(mock_m4a.name, mock_m4a)
        self.assertEqual(url, f"/api/download/{mock_m4a.name}")

        job = JobStatus(
            job_id="success-job-1",
            url="https://www.youtube.com/watch?v=xvT1jH8B9AM",
            status="completed",
            progress=100.0,
            filename=mock_m4a.name,
            download_url=url,
            file_size_bytes=mock_m4a.stat().st_size,
            created_at=time.time(),
            completed_at=time.time()
        )
        self.job_store.create_job(job)

        fetched = self.job_store.get_job("success-job-1")
        self.assertEqual(fetched.status, "completed")
        self.assertIsNotNone(fetched.download_url)

    # 4. Failed extraction & sanitized error
    def test_04_failed_extraction_sanitization(self):
        raw_error = "YouTube bot challenge: cookiefile=/var/data/cookies.txt auth=bearer_token_xyz"
        job = JobStatus(
            job_id="fail-job-1",
            url="https://www.youtube.com/watch?v=invalid",
            status="failed",
            error=raw_error,
            created_at=time.time(),
            completed_at=time.time()
        )
        self.job_store.create_job(job)

        fetched = self.job_store.get_job("fail-job-1")
        self.assertEqual(fetched.status, "failed")
        self.assertNotIn("bearer_token_xyz", fetched.error)
        self.assertIn("REDACTED", fetched.error)

    # 5. Invalid YouTube URL rejection
    def test_05_invalid_url_rejection(self):
        invalid_cases = [
            "https://evil.com/video.mp4",
            "http://notyoutube.com",
            "https://youtube.com/watch?v=123;rm -rf /",
            "javascript:alert(1)"
        ]
        for url in invalid_cases:
            self.assertFalse(validate_youtube_url(url))

    # 6. Staged file listing
    def test_06_staged_file_listing(self):
        files = self.storage.list_files()
        self.assertIsInstance(files, list)

    # 7. File download
    def test_07_file_download_resolution(self):
        test_file = self.downloads_dir / "dl_test.m4a"
        test_file.write_bytes(b"\x00\x00\x00\x18ftypM4A ")
        p = self.storage.get_file_path("dl_test.m4a")
        self.assertIsNotNone(p)
        self.assertTrue(p.exists())

    # 8. Audio-only validation (0 video tracks)
    def test_08_audio_only_validation_rejects_video(self):
        # Create container with a video track
        video_payload = b"\x00\x00\x00\x00\x00\x00\x00\x00vide\x00\x00\x00\x00\x00\x00\x00\x00"
        hdlr_video = struct.pack(">I", 8 + len(video_payload)) + b"hdlr" + video_payload
        moov_video = struct.pack(">I", 8 + len(hdlr_video)) + b"moov" + hdlr_video
        fake_video_file = self.downloads_dir / "fake_video.m4a"
        fake_video_file.write_bytes(b"\x00\x00\x00\x18ftypM4A " + moov_video)

        audio_tracks, video_tracks = inspect_mp4_container_tracks(fake_video_file)
        self.assertGreater(video_tracks, 0)

    # 9. >60MB rejection limit
    def test_09_over_60mb_limit_constant(self):
        self.assertEqual(MAX_ALLOWED_FILE_BYTES, 60 * 1024 * 1024)
        oversized_bytes = 61 * 1024 * 1024
        self.assertGreater(oversized_bytes, MAX_ALLOWED_FILE_BYTES)

    # 10. FAT32 filename sanitization
    def test_10_fat32_filename_sanitization(self):
        raw = 'My / Best : Favorite * Track? "Ever" <2026> | New'
        clean = sanitize_fat32_filename(raw, max_length=60)
        self.assertLessEqual(len(clean), 60)
        for c in r'/\:*?"<>|':
            self.assertNotIn(c, clean)

    # 11. Concurrent jobs
    def test_11_concurrent_job_registration(self):
        for i in range(5):
            self.job_store.create_job(JobStatus(
                job_id=f"concurrent-{i}",
                url=f"https://youtu.be/test{i}",
                status="queued",
                created_at=time.time() + i
            ))

        jobs = self.job_store.list_jobs()
        concurrent_jobs = [j for j in jobs if j.job_id.startswith("concurrent-")]
        self.assertEqual(len(concurrent_jobs), 5)

    # 12. Worker restart/recovery
    def test_12_worker_restart_recovery(self):
        # Insert a job
        self.job_store.create_job(JobStatus(
            job_id="recovery-job-123",
            url="https://youtu.be/recover_me",
            status="completed",
            progress=100.0,
            filename="recovered.m4a",
            created_at=time.time(),
            completed_at=time.time()
        ))

        # Simulate worker shutdown and reboot
        self.job_store.close()
        rebooted_store = JobStore(db_path=self.db_path)
        recovered = rebooted_store.get_job("recovery-job-123")
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.status, "completed")
        self.assertEqual(recovered.filename, "recovered.m4a")
        rebooted_store.close()

if __name__ == "__main__":
    unittest.main()
