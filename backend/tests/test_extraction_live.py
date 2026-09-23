import os
import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.extractor import AudioExtractor, jobs
from app.models import JobStatus

def test_live_extraction():
    # Short test video (YouTube's official short audio/video test or standard sample)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ" # Big Buck Bunny 30s teaser / sample
    extractor = AudioExtractor()
    job_id = "test-job-001"
    jobs[job_id] = JobStatus(
        job_id=job_id,
        url=test_url,
        status="queued",
        created_at=time.time()
    )
    print(f"Testing extraction from: {test_url}")
    result = extractor.extract_sync(job_id=job_id, url=test_url, format_pref="m4a")
    print(f"Status: {result.status}")
    if result.status == "completed":
        print(f"Filename: {result.filename}")
        print(f"Size: {result.file_size_bytes} bytes")
        target_path = extractor.downloads_dir / result.filename
        assert target_path.exists(), "Extracted file does not exist on disk"
        print("✓ Extraction verified! File exists on disk.")
    else:
        print(f"Notice: Extraction ended with status: {result.status}, error: {result.error}")

if __name__ == "__main__":
    test_live_extraction()
