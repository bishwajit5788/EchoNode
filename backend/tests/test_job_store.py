import sys
import tempfile
import time
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import JobStatus
from app.services.job_store import JobStore, sanitize_error_message

class TestJobStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_jobs.db"
        self.store = JobStore(db_path=self.db_path)

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_create_and_get_job(self):
        job = JobStatus(
            job_id="test-job-1",
            url="https://www.youtube.com/watch?v=xvT1jH8B9AM",
            status="queued",
            progress=0.0,
            created_at=time.time()
        )
        self.store.create_job(job)

        fetched = self.store.get_job("test-job-1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.job_id, "test-job-1")
        self.assertEqual(fetched.status, "queued")
        self.assertEqual(fetched.progress, 0.0)

    def test_persistence_across_store_instances(self):
        job = JobStatus(
            job_id="persisted-job",
            url="https://youtu.be/xvT1jH8B9AM",
            status="processing",
            progress=45.5,
            created_at=time.time()
        )
        self.store.create_job(job)

        # Create a new instance pointing to the same SQLite file
        second_store = JobStore(db_path=self.db_path)
        fetched = second_store.get_job("persisted-job")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, "processing")
        self.assertEqual(fetched.progress, 45.5)
        second_store.close()

    def test_job_lifecycle_transitions(self):
        job_id = "lifecycle-job"
        job = JobStatus(
            job_id=job_id,
            url="https://youtube.com/watch?v=aqz-KE-bpKQ",
            status="queued",
            created_at=time.time()
        )
        self.store.create_job(job)

        # Transition to processing
        self.store.update_job(job_id, status="processing", progress=25.0)
        j1 = self.store.get_job(job_id)
        self.assertEqual(j1.status, "processing")
        self.assertEqual(j1.progress, 25.0)

        # Transition to completed
        self.store.update_job(
            job_id,
            status="completed",
            progress=100.0,
            filename="test_track.m4a",
            download_url="/api/download/test_track.m4a",
            file_size_bytes=1048576,
            completed_at=time.time()
        )
        j2 = self.store.get_job(job_id)
        self.assertEqual(j2.status, "completed")
        self.assertEqual(j2.progress, 100.0)
        self.assertEqual(j2.filename, "test_track.m4a")
        self.assertEqual(j2.download_url, "/api/download/test_track.m4a")

    def test_error_sanitization(self):
        raw_error = (
            "Error in /Users/john_doe/EchoNode/backend:\n"
            ".youtube.com TRUE / FALSE 1700000000 SAPISID abcdef1234567890\n"
            "Failed with token=secret_token_123456"
        )
        sanitized = sanitize_error_message(raw_error)

        self.assertNotIn("SAPISID abcdef", sanitized)
        self.assertNotIn("secret_token_123456", sanitized)
        self.assertNotIn("john_doe", sanitized)
        self.assertIn("[REDACTED", sanitized)
        self.assertIn("/Users/[USER]", sanitized)

    def test_update_sanitizes_stored_error(self):
        job_id = "failed-job"
        job = JobStatus(
            job_id=job_id,
            url="https://youtube.com/watch?v=test",
            status="queued",
            created_at=time.time()
        )
        self.store.create_job(job)

        leak_error = "YouTube Bot Block: cookiefile=/tmp/cookies.txt auth=bearer_token_xyz123"
        self.store.update_job(job_id, status="failed", error=leak_error)

        stored = self.store.get_job(job_id)
        self.assertEqual(stored.status, "failed")
        self.assertNotIn("bearer_token_xyz123", stored.error)
        self.assertIn("REDACTED", stored.error)

    def test_list_and_delete_jobs(self):
        for i in range(3):
            self.store.create_job(JobStatus(
                job_id=f"job-{i}",
                url=f"https://youtu.be/{i}",
                status="queued",
                created_at=time.time() + i
            ))

        jobs = self.store.list_jobs()
        self.assertEqual(len(jobs), 3)

        deleted = self.store.delete_job("job-1")
        self.assertTrue(deleted)
        self.assertIsNone(self.store.get_job("job-1"))
        self.assertEqual(len(self.store.list_jobs()), 2)

if __name__ == "__main__":
    unittest.main()
