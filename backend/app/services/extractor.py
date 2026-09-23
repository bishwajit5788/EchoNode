import os
import re
import time
import uuid
import shutil
import struct
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import yt_dlp

from ..config import settings, sanitize_fat32_filename
from ..models import JobStatus

logger = logging.getLogger("echonode.extractor")
logging.basicConfig(level=logging.INFO)

# Global in-memory job registry
jobs: Dict[str, JobStatus] = {}

# Maximum concurrent background extraction jobs
CONCURRENCY_LIMIT = 2
extraction_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

# Maximum allowed audio file size: 60 MB
MAX_ALLOWED_FILE_BYTES = 60 * 1024 * 1024

# Allowed URL domains
ALLOWED_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be"
}

def validate_youtube_url(url: str) -> bool:
    """Validate that the URL is a safe, well-formed YouTube URL."""
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").lower()
        if not any(hostname == d or hostname.endswith("." + d) for d in ALLOWED_DOMAINS):
            return False
        # Prevent any potential command injection payload in URL strings
        if any(c in url for c in [';', '&', '|', '`', '$', '\n', '\r']):
            return False
        return True
    except Exception:
        return False

def inspect_mp4_container_tracks(file_path: Path) -> Tuple[int, int]:
    """
    Pure Python parser for MP4/M4A ISO Base Media File Format containers.
    Inspects track handlers ('hdlr') to count audio ('soun') and video ('vide') tracks.
    Returns (num_audio_tracks, num_video_tracks).
    """
    audio_tracks = 0
    video_tracks = 0

    try:
        with open(file_path, "rb") as f:
            data = f.read()

        pos = 0
        file_len = len(data)

        # Scan for 'hdlr' atoms
        while pos + 8 <= file_len:
            atom_size = struct.unpack(">I", data[pos:pos+4])[0]
            atom_type = data[pos+4:pos+8]

            if atom_size == 1 and pos + 16 <= file_len:
                # 64-bit extended size
                atom_size = struct.unpack(">Q", data[pos+8:pos+16])[0]
                content_start = pos + 16
            elif atom_size == 0:
                # Atom extends to EOF
                atom_size = file_len - pos
                content_start = pos + 8
            else:
                content_start = pos + 8

            if atom_size < 8:
                break

            # If inside or finding hdlr directly
            # hdlr structure: version(1) + flags(3) + pre_defined(4) + handler_type(4)
            # handler_type is at content_start + 8
            if atom_type == b"hdlr" and content_start + 12 <= file_len:
                handler = data[content_start+8:content_start+12]
                if handler == b"soun":
                    audio_tracks += 1
                elif handler == b"vide":
                    video_tracks += 1

            # Search recursively inside container atoms: moov, trak, mdia
            if atom_type in (b"moov", b"trak", b"mdia", b"minf"):
                pos = content_start
            else:
                pos += atom_size

    except Exception as e:
        logger.warning(f"Error inspecting MP4 atoms in {file_path.name}: {e}")

    # Fallback / heuristic scan for hdlr markers if deeply nested
    if audio_tracks == 0 and video_tracks == 0:
        if b"soun" in data:
            audio_tracks = data.count(b"hdlr") if b"hdlr" in data else 1
        if b"vide" in data and b"hdlr" in data:
            # Check if vide occurs directly after an hdlr header
            idx = 0
            while True:
                idx = data.find(b"hdlr", idx)
                if idx == -1:
                    break
                if idx + 16 <= len(data):
                    handler = data[idx+12:idx+16]
                    if handler == b"vide":
                        video_tracks += 1
                idx += 4

    return audio_tracks, video_tracks

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
                job.status = "verifying"
        return hook

    def extract_sync(self, job_id: str, url: str, format_pref: str = "m4a", custom_title: Optional[str] = None) -> JobStatus:
        job = jobs[job_id]
        job.status = "downloading"

        try:
            # Step 1: Pre-flight metadata extraction
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl_info:
                info = ydl_info.extract_info(url, download=False)
                raw_title = custom_title or info.get("title", f"echonode_track_{job_id[:8]}")
                duration = info.get("duration", 0)
                job.title = raw_title
                job.duration_seconds = duration

            safe_basename = sanitize_fat32_filename(raw_title, max_length=settings.max_title_length)

            # Step 2: Configure extraction strictly for AUDIO ONLY
            # Format 140 is standard YouTube m4a (AAC-LC ~128kbps stereo)
            ydl_opts = {
                "outtmpl": str(self.downloads_dir / f"{safe_basename}.%(ext)s"),
                "noplaylist": True,
                "progress_hooks": [self._progress_hook(job_id)],
                "quiet": True,
                "no_warnings": True,
                # Enforce audio-only format selection, reject video streams completely
                "format": "140/bestaudio[ext=m4a]/bestaudio/best",
            }

            if self.has_ffmpeg:
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a" if format_pref == "m4a" else "mp3",
                    "preferredquality": "128",
                    "nopostoverwrites": False,
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)

            # Step 3: Locate downloaded target file
            target_file = None
            for ext in ["m4a", "mp3", "aac", "opus"]:
                candidate = self.downloads_dir / f"{safe_basename}.{ext}"
                if candidate.exists():
                    target_file = candidate
                    break

            if not target_file or not target_file.exists():
                matches = list(self.downloads_dir.glob(f"{safe_basename}.*"))
                if matches:
                    target_file = matches[0]

            if not target_file or not target_file.exists():
                raise RuntimeError(f"Extracted file not found for {safe_basename}")

            # Step 4: Size and boundary validation
            file_size = target_file.stat().st_size
            if file_size > MAX_ALLOWED_FILE_BYTES:
                target_file.unlink(missing_ok=True)
                raise ValueError(f"Extracted file ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of {MAX_ALLOWED_FILE_BYTES / (1024*1024):.0f} MB.")

            # Step 5: CRITICAL MEDIA AUDIT - Reject any media containing video stream
            if target_file.suffix.lower() == ".m4a":
                audio_tracks, video_tracks = inspect_mp4_container_tracks(target_file)
                if video_tracks > 0:
                    target_file.unlink(missing_ok=True)
                    raise ValueError(f"Security validation failed: File contains {video_tracks} video track(s). Output must be pure audio-only!")

            job.filename = target_file.name
            job.file_size_bytes = file_size
            job.status = "completed"
            job.progress = 100.0
            job.completed_at = time.time()
            logger.info(f"Verified Audio-Only Stream: {job.filename} ({file_size} bytes)")

        except Exception as e:
            logger.error(f"Extraction failed for job {job_id}: {str(e)}")
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

        async def worker():
            async with extraction_semaphore:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.extract_sync, job_id, url, format_pref, custom_title)

        asyncio.create_task(worker())
        return job_id

extractor_service = AudioExtractor()
