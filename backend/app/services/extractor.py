import os
import re
import time
import uuid
import shutil
import struct
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse
import yt_dlp

from ..config import settings, sanitize_fat32_filename
from ..models import JobStatus
from .job_store import job_store, sanitize_error_message
from .storage import storage_service

logger = logging.getLogger("echonode.extractor")
logging.basicConfig(level=logging.INFO)

# Maximum concurrent extraction jobs
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

        # Scan for atoms
        while pos + 8 <= file_len:
            atom_size = struct.unpack(">I", data[pos:pos+4])[0]
            atom_type = data[pos+4:pos+8]

            if atom_size == 1 and pos + 16 <= file_len:
                atom_size = struct.unpack(">Q", data[pos+8:pos+16])[0]
                content_start = pos + 16
            elif atom_size == 0:
                atom_size = file_len - pos
                content_start = pos + 8
            else:
                content_start = pos + 8

            if atom_size < 8:
                break

            # hdlr structure: version(1) + flags(3) + pre_defined(4) + handler_type(4)
            if atom_type == b"hdlr" and content_start + 12 <= file_len:
                handler = data[content_start+8:content_start+12]
                if handler == b"soun":
                    audio_tracks += 1
                elif handler == b"vide":
                    video_tracks += 1

            # Search recursively inside container atoms: moov, trak, mdia, minf
            if atom_type in (b"moov", b"trak", b"mdia", b"minf"):
                pos = content_start
            else:
                pos += atom_size

    except Exception as e:
        logger.warning(f"Error inspecting MP4 atoms in {file_path.name}: {e}")

    # Fallback scan for hdlr markers if deeply nested
    if audio_tracks == 0 and video_tracks == 0:
        if b"soun" in data:
            audio_tracks = data.count(b"hdlr") if b"hdlr" in data else 1
        if b"vide" in data and b"hdlr" in data:
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
    return job_store.get_job(job_id)

def list_jobs() -> List[JobStatus]:
    return job_store.list_jobs()

class AudioExtractor:
    def __init__(self, downloads_dir: Optional[Path] = None):
        self.downloads_dir = downloads_dir or settings.downloads_dir
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.has_ffmpeg = shutil.which("ffmpeg") is not None

    def _progress_hook(self, job_id: str):
        def hook(d: dict):
            status = d.get("status")
            if status == "downloading":
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_bytes = d.get("downloaded_bytes", 0)
                prog = 0.0
                if total_bytes > 0:
                    prog = round((downloaded_bytes / total_bytes) * 100, 1)
                else:
                    percent_str = d.get("_percent_str", "0%").strip().replace("%", "")
                    try:
                        prog = float(percent_str)
                    except ValueError:
                        pass
                job_store.update_job(job_id, status="processing", progress=prog)
            elif status == "finished":
                job_store.update_job(job_id, status="processing", progress=99.0)
        return hook

    def extract_sync(self, job_id: str, url: str, format_pref: str = "m4a", custom_title: Optional[str] = None) -> JobStatus:
        job_store.update_job(job_id, status="processing", progress=5.0)
        temp_cookie_file = None

        try:
            # Step 1: Pre-flight metadata extraction
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl_info:
                info = ydl_info.extract_info(url, download=False)
                raw_title = custom_title or info.get("title", f"echonode_track_{job_id[:8]}")
                duration = info.get("duration", 0)
                job_store.update_job(job_id, title=raw_title, duration_seconds=duration, progress=10.0)

            safe_basename = sanitize_fat32_filename(raw_title, max_length=settings.max_title_length)

            # Step 2: Configure extraction strictly for AUDIO ONLY
            # Format 140 is standard YouTube m4a (AAC-LC ~128kbps stereo)
            ydl_opts = {
                "outtmpl": str(self.downloads_dir / f"{safe_basename}.%(ext)s"),
                "noplaylist": True,
                "progress_hooks": [self._progress_hook(job_id)],
                "quiet": True,
                "no_warnings": True,
                "format": "140/bestaudio[ext=m4a]/bestaudio/best",
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "mweb", "web"]
                    }
                },
            }

            # Secure cookie authentication handling
            cookies_data = os.environ.get("YTDLP_COOKIES")
            cookies_path_env = os.environ.get("YTDLP_COOKIES_PATH")

            if cookies_data:
                # Write to private temp file with 0600 mode
                fd, tmp_path = tempfile.mkstemp(prefix="yt_sec_", suffix=".cookies")
                with os.fdopen(fd, "w") as f:
                    f.write(cookies_data)
                os.chmod(tmp_path, 0o600)
                temp_cookie_file = tmp_path
                ydl_opts["cookiefile"] = tmp_path
            elif cookies_path_env and Path(cookies_path_env).exists():
                ydl_opts["cookiefile"] = str(Path(cookies_path_env).resolve())
            else:
                # Check for gitignored local cookies files in backend directory
                local_candidates = [
                    settings.downloads_dir.parent / "cookies.txt",
                    settings.downloads_dir.parent / ".cookies",
                ]
                for cand in local_candidates:
                    if cand.exists():
                        ydl_opts["cookiefile"] = str(cand.resolve())
                        break

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

            # Step 4: Size and boundary validation (<= 60MB)
            file_size = target_file.stat().st_size
            if file_size > MAX_ALLOWED_FILE_BYTES:
                target_file.unlink(missing_ok=True)
                raise ValueError(
                    f"Extracted file ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of {MAX_ALLOWED_FILE_BYTES / (1024*1024):.0f} MB."
                )

            # Step 5: CRITICAL MEDIA AUDIT - Reject any media containing video stream
            if target_file.suffix.lower() == ".m4a":
                audio_tracks, video_tracks = inspect_mp4_container_tracks(target_file)
                if video_tracks > 0:
                    target_file.unlink(missing_ok=True)
                    raise ValueError(f"Security validation failed: File contains {video_tracks} video track(s). Output must be pure audio-only!")

            # Step 6: Persist file via StorageService and get stable download URL
            download_url = storage_service.save_file(
                filename=target_file.name,
                source_path=target_file,
                content_type="audio/mp4" if target_file.suffix.lower() == ".m4a" else "audio/mpeg"
            )

            job = job_store.update_job(
                job_id,
                filename=target_file.name,
                download_url=download_url,
                file_size_bytes=file_size,
                status="completed",
                progress=100.0,
                completed_at=time.time(),
                error=None
            )
            logger.info(f"Verified Audio-Only Stream: {target_file.name} ({file_size} bytes)")
            return job or job_store.get_job(job_id)

        except Exception as e:
            raw_err = str(e)
            logger.error(f"Extraction failed for job {job_id}: {sanitize_error_message(raw_err)}")
            job = job_store.update_job(
                job_id,
                status="failed",
                error=raw_err,
                completed_at=time.time()
            )
            return job or job_store.get_job(job_id)

        finally:
            # Always shred/remove temporary cookie file
            if temp_cookie_file and os.path.exists(temp_cookie_file):
                try:
                    os.unlink(temp_cookie_file)
                except Exception:
                    pass

    async def start_extraction_job(
        self,
        url: str,
        format_pref: str = "m4a",
        custom_title: Optional[str] = None,
        wait_for_completion: bool = False
    ) -> str:
        job_id = str(uuid.uuid4())
        job = JobStatus(
            job_id=job_id,
            url=url,
            status="queued",
            progress=0.0,
            created_at=time.time()
        )
        job_store.create_job(job)

        if wait_for_completion:
            loop = asyncio.get_running_loop()
            async with extraction_semaphore:
                await loop.run_in_executor(None, self.extract_sync, job_id, url, format_pref, custom_title)
        else:
            async def worker():
                async with extraction_semaphore:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, self.extract_sync, job_id, url, format_pref, custom_title)

            asyncio.create_task(worker())

        return job_id

extractor_service = AudioExtractor()
