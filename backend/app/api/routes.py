import os
import shutil
import urllib.parse
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse

from ..config import settings
from ..models import (
    ExtractionRequest,
    ExtractionResponse,
    JobStatus,
    AudioFileItem,
    SyncRequest,
    SyncResponse
)
from ..services.extractor import extractor_service, get_job, list_jobs, validate_youtube_url

router = APIRouter(prefix="/api", tags=["EchoNode Audio Engine"])

@router.post("/extract", response_model=ExtractionResponse)
async def submit_extraction(request: ExtractionRequest):
    """Submit a YouTube URL to extract into an audio-only container."""
    url = request.url.strip()
    if not validate_youtube_url(url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid or unsupported URL. Must be a valid HTTP/HTTPS link from youtube.com or youtu.be"
        )

    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    job_id = await extractor_service.start_extraction_job(
        url=url,
        format_pref=request.format_preference or "m4a",
        custom_title=request.custom_title,
        wait_for_completion=is_serverless
    )

    job = get_job(job_id)
    status_str = job.status if (is_serverless and job) else "queued"
    msg = "Audio extracted and validated successfully" if status_str == "completed" else "Audio extraction job queued successfully"
    if status_str == "failed" and job and job.error:
        msg = f"Extraction failed: {job.error}"

    return ExtractionResponse(
        job_id=job_id,
        message=msg,
        status=status_str
    )

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Retrieve progress and completion state of an extraction job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Extraction job not found")
    return job

@router.get("/jobs", response_model=List[JobStatus])
async def get_all_jobs():
    """Retrieve all jobs tracked in this session."""
    return list(list_jobs().values())

@router.get("/files", response_model=List[AudioFileItem])
async def list_audio_files():
    """List all extracted audio files ready for SD transfer."""
    files: List[AudioFileItem] = []
    if not settings.downloads_dir.exists():
        return files

    valid_extensions = {".m4a", ".mp3", ".aac", ".ogg", ".opus"}
    for path in sorted(settings.downloads_dir.iterdir(), key=os.path.getmtime, reverse=True):
        if path.is_file() and path.suffix.lower() in valid_extensions:
            stat = path.stat()
            quoted_filename = urllib.parse.quote(path.name)
            files.append(AudioFileItem(
                filename=path.name,
                title=path.stem.replace("_", " "),
                size_bytes=stat.st_size,
                extension=path.suffix.lower().lstrip("."),
                download_url=f"/api/download/{quoted_filename}",
                sd_ready=True,
                created_at=stat.st_mtime
            ))
    return files

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Stream or download a specific audio track."""
    unquoted_name = urllib.parse.unquote(filename)
    # Prevent path traversal
    safe_path = (settings.downloads_dir / unquoted_name).resolve()
    if not str(safe_path).startswith(str(settings.downloads_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="Requested audio track not found")

    media_type = "audio/mp4" if safe_path.suffix.lower() == ".m4a" else "audio/mpeg"
    return FileResponse(
        path=safe_path,
        media_type=media_type,
        filename=safe_path.name
    )

@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete an audio track from the local staging storage."""
    unquoted_name = urllib.parse.unquote(filename)
    safe_path = (settings.downloads_dir / unquoted_name).resolve()
    if not str(safe_path).startswith(str(settings.downloads_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    safe_path.unlink()
    return {"message": f"Successfully deleted {unquoted_name}"}

@router.post("/sync-sd", response_model=SyncResponse)
async def sync_to_sd(req: SyncRequest):
    """Copy all staged audio files to a mounted MicroSD card path."""
    dest = Path(req.target_path)
    if not dest.exists() or not dest.is_dir():
        raise HTTPException(status_code=400, detail=f"Target path does not exist or is not a directory: {req.target_path}")

    copied = 0
    failed = 0
    valid_extensions = {".m4a", ".mp3", ".aac"}
    for f in settings.downloads_dir.iterdir():
        if f.is_file() and f.suffix.lower() in valid_extensions:
            try:
                dest_file = dest / f.name
                shutil.copy2(f, dest_file)
                copied += 1
            except Exception:
                failed += 1

    return SyncResponse(
        copied_count=copied,
        failed_count=failed,
        target_path=str(dest),
        message=f"Sync completed. Copied {copied} files ({failed} failed)."
    )

@router.get("/system-info")
async def system_info():
    """System capabilities and storage diagnostics."""
    total_files = len(list(settings.downloads_dir.glob("*.*")))
    total_size = sum(f.stat().st_size for f in settings.downloads_dir.glob("*.*") if f.is_file())
    return {
        "app": settings.app_name,
        "version": settings.version,
        "ffmpeg_available": extractor_service.has_ffmpeg,
        "downloads_dir": str(settings.downloads_dir),
        "total_files": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "sd_format_standard": "FAT32 (<=32GB recommended)",
    }
