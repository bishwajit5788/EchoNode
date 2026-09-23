import os
import time
import uuid
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
import yt_dlp

from ..config import settings, sanitize_fat32_filename
from ..models import JobStatus

logger = logging.getLogger("echonode.extractor")
logging.basicConfig(level=logging.INFO)

# Global in-memory job registry
jobs: Dict[str, JobStatus] = {}

def get_job(job_id: str) -> Optional[JobStatus]:
    return jobs.get(job_id)

def list_jobs() -> Dict[str, JobStatus]:
    return jobs

class AudioExtractor:
    def __init__(self, downloads_dir: Optional[Path] = None):
        self.downloads_dir = downloads_dir or settings.downloads_dir
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.has_ffmpeg = shutil.which("ffmpeg") is not None

    def _progress_hook(self, job_id: str):
        def hook(d: dict):
            job = jobs.get(job_id)
            if not job:
                return

            status = d.get("status")
            if status == "downloading":
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_bytes = d.get("downloaded_bytes", 0)
                if total_bytes > 0:
                    job.progress = round((downloaded_bytes / total_bytes) * 100, 1)
                else:
                    percent_str = d.get("_percent_str", "0%").strip().replace("%", "")
                    try:
                        job.progress = float(percent_str)
                    except ValueError:
                        pass
                job.status = "downloading"
            elif status == "finished":
                job.progress = 100.0
                job.status = "finalizing"
        return hook

    def extract_sync(self, job_id: str, url: str, format_pref: str = "m4a", custom_title: Optional[str] = None) -> JobStatus:
        job = jobs[job_id]
        job.status = "downloading"

        try:
            # First extract basic metadata to construct sanitized FAT32 filename
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl_info:
                info = ydl_info.extract_info(url, download=False)
                raw_title = custom_title or info.get("title", f"echonode_track_{job_id[:8]}")
                duration = info.get("duration", 0)
                job.title = raw_title
                job.duration_seconds = duration

            safe_basename = sanitize_fat32_filename(raw_title, max_length=settings.max_title_length)
            
            # Format selection strategy:
            # 140 is standard YouTube m4a (AAC-LC ~128kbps stereo) - perfectly compatible with ESP32-audioI2S.
            # If ffmpeg is absent, we strictly download native audio streams without recoding.
            ydl_opts = {
                "outtmpl": str(self.downloads_dir / f"{safe_basename}.%(ext)s"),
                "noplaylist": True,
                "progress_hooks": [self._progress_hook(job_id)],
                "quiet": True,
                "no_warnings": True,
            }

            if self.has_ffmpeg:
                # With ffmpeg: extract and ensure clean m4a container (AAC)
                ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a" if format_pref == "m4a" else "mp3",
                    "preferredquality": "128",
                    "nopostoverwrites": False,
                }]
            else:
                # Without ffmpeg: grab standard audio-only stream (itag 140 is m4a, fallback to best audio)
                ydl_opts["format"] = "140/bestaudio[ext=m4a]/bestaudio/best"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                download_res = ydl.extract_info(url, download=True)
                # Find output filename
                expected_ext = "m4a" if (format_pref == "m4a" or not self.has_ffmpeg) else format_pref
                
                # Check actual downloaded file on disk
                target_file = None
                for ext in [expected_ext, "m4a", "webm", "opus", "mp3"]:
                    candidate = self.downloads_dir / f"{safe_basename}.{ext}"
                    if candidate.exists():
                        target_file = candidate
                        break

                if not target_file or not target_file.exists():
                    # Fallback search by prefix
                    matches = list(self.downloads_dir.glob(f"{safe_basename}.*"))
                    if matches:
                        target_file = matches[0]

                if not target_file or not target_file.exists():
                    raise RuntimeError(f"Extracted file not found for {safe_basename}")

                job.filename = target_file.name
                job.file_size_bytes = target_file.stat().st_size
                job.status = "completed"
                job.progress = 100.0
                job.completed_at = time.time()
                logger.info(f"Successfully extracted: {job.filename} ({job.file_size_bytes} bytes)")

        except Exception as e:
            logger.error(f"Extraction failed for job {job_id}: {str(e)}", exc_info=True)
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()

        return job

    async def start_extraction_job(self, url: str, format_pref: str = "m4a", custom_title: Optional[str] = None) -> str:
        job_id = str(uuid.uuid4())
        job = JobStatus(
            job_id=job_id,
            url=url,
            status="queued",
            progress=0.0,
            created_at=time.time()
        )
        jobs[job_id] = job

        # Launch in background thread to keep FastAPI loop responsive
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, self.extract_sync, job_id, url, format_pref, custom_title)
        return job_id

extractor_service = AudioExtractor()
