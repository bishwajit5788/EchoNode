import os
import sys
import time
import asyncio
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.extractor import extractor_service, inspect_mp4_container_tracks
from app.services.job_store import job_store
from app.services.storage import storage_service
from app.api.routes import submit_extraction, get_job_status, list_audio_files
from app.models import ExtractionRequest

async def run_real_e2e_extraction():
    print("=" * 60)
    print("PHASE 12 — REAL END-TO-END TEST ON EXTRACTION PIPELINE")
    print("=" * 60)

    # Use Big Buck Bunny (official open-source public creative commons video)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    # Ensure local extraction mode for direct execution test
    os.environ["EXTRACTION_MODE"] = "local"
    if "WORKER_URL" in os.environ:
        del os.environ["WORKER_URL"]

    # 1. POST /api/extract
    print(f"\n1. Submitting extraction request for URL: {test_url}")
    req = ExtractionRequest(
        url=test_url,
        format_preference="m4a",
        custom_title="Big Buck Bunny CC Test"
    )

    resp = await submit_extraction(req)
    job_id = resp.job_id
    print(f"\n2. Received Job ID: {job_id} | Initial Status: {resp.status}")

    # 3. Poll job until completion
    print("3. Polling job status...")
    max_wait = 90
    start_time = time.time()
    final_job = None

    while time.time() - start_time < max_wait:
        job = await get_job_status(job_id)
        status = job.status
        progress = job.progress
        print(f"   [+{int(time.time() - start_time)}s] Status: {status} | Progress: {progress}%")

        if status in ("completed", "failed"):
            final_job = job
            break
        await asyncio.sleep(2)

    assert final_job is not None, "Job timed out before reaching a terminal status"
    print(f"\n4. Job reached terminal status: {final_job.status}")
    if final_job.status == "failed":
        print(f"   Extraction error: {final_job.error}")
        sys.exit(1)

    assert final_job.status == "completed", f"Job failed: {final_job.error}"

    # 5. Retrieve staged file list
    print("\n5. Retrieving staged audio files list...")
    staged_files = await list_audio_files()
    print(f"   Found {len(staged_files)} staged audio file(s)")

    # 6. Locate resulting M4A
    filename = final_job.filename
    print(f"\n6. Locating generated file: {filename}")
    found = any(f.filename == filename for f in staged_files)
    assert found, f"Generated file {filename} not listed in /api/files"

    # 7 & 8. Verify file exists on disk
    file_path = storage_service.get_file_path(filename)
    assert file_path is not None and file_path.exists(), "File does not exist on disk"
    print(f"   ✓ File exists on disk: {file_path}")

    # 9. Verify <= 60 MB
    file_size = file_path.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"\n9. File size: {file_size} bytes ({size_mb:.2f} MB)")
    assert file_size <= 60 * 1024 * 1024, f"File exceeds 60 MB limit: {file_size} bytes"
    print("   ✓ File size is <= 60 MB")

    # 10, 11, 12, 13. Container atom verification
    print("\n10. Inspecting ISO Base Media File Format container atoms...")
    audio_tracks, video_tracks = inspect_mp4_container_tracks(file_path)
    print(f"   Audio Tracks Detected: {audio_tracks}")
    print(f"   Video Tracks Detected: {video_tracks}")
    assert audio_tracks >= 1, "Verification failed: No audio stream found"
    assert video_tracks == 0, f"Verification failed: Contains {video_tracks} video track(s)"
    print("   ✓ Verified pure audio stream (audio_tracks >= 1)")
    print("   ✓ Verified pure video-free stream (video_tracks == 0)")
    print("   ✓ Verified valid M4A container")

    # 14. Verify job remains completed after re-query (simulating refresh)
    print("\n14. Simulating frontend page reload / re-query...")
    recheck = await get_job_status(job_id)
    assert recheck.status == "completed"
    assert recheck.filename == filename
    print("   ✓ Job state persisted and verified in JobStore across requests")

    print("\n" + "=" * 60)
    print("ALL REAL EXTRACTION VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_real_e2e_extraction())
