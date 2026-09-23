import os
import json
import shutil
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, RedirectResponse

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
from ..services.job_store import job_store, sanitize_error_message
from ..services.storage import storage_service

router = APIRouter(prefix="/api", tags=["EchoNode Audio Engine"])

WORKER_URL = os.environ.get("WORKER_URL", "").strip().rstrip("/")

def proxy_to_worker(method: str, path: str, payload: Optional[dict] = None) -> dict:
    """Forward an API request to the dedicated persistent extraction worker."""
    target_url = f"{WORKER_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None

    req = urllib.request.Request(target_url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            detail = err_json.get("detail", err_json.get("message", str(e)))
        except Exception:
            detail = err_body or str(e)
        raise HTTPException(status_code=e.code, detail=sanitize_error_message(detail))
    except urllib.error.URLError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Persistent extraction worker is currently unreachable: {sanitize_error_message(str(e.reason))}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=sanitize_error_message(str(e)))

@router.post("/extract", response_model=ExtractionResponse)
async def submit_extraction(request: ExtractionRequest):
    """Submit a YouTube URL to extract into an audio-only container."""
    url = request.url.strip()
    if not validate_youtube_url(url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid or unsupported URL. Must be a valid HTTP/HTTPS link from youtube.com or youtu.be"
        )

    # If configured with a standalone persistent worker, forward request to worker
    if WORKER_URL:
        resp = proxy_to_worker("POST", "/api/extract", request.model_dump())
        return ExtractionResponse(**resp)

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
    if WORKER_URL:
        resp = proxy_to_worker("GET", f"/api/jobs/{job_id}")
        return JobStatus(**resp)

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Extraction job not found")
    return job

@router.get("/jobs", response_model=List[JobStatus])
async def get_all_jobs():
    """Retrieve all jobs tracked in this persistent store."""
    if WORKER_URL:
        resp = proxy_to_worker("GET", "/api/jobs")
        return [JobStatus(**item) for item in resp]

    return list_jobs()

@router.get("/files", response_model=List[AudioFileItem])
async def list_audio_files():
    """List all extracted audio files ready for SD transfer."""
    if WORKER_URL:
        resp = proxy_to_worker("GET", "/api/files")
        return [AudioFileItem(**item) for item in resp]

    return storage_service.list_files()

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Stream or redirect to download a specific audio track."""
    unquoted_name = urllib.parse.unquote(filename)

    if WORKER_URL:
        worker_download = f"{WORKER_URL}/api/download/{urllib.parse.quote(unquoted_name)}"
        return RedirectResponse(url=worker_download)

    local_path = storage_service.get_file_path(unquoted_name)
    if local_path and local_path.exists():
        media_type = "audio/mp4" if local_path.suffix.lower() == ".m4a" else "audio/mpeg"
        return FileResponse(
            path=local_path,
            media_type=media_type,
            filename=local_path.name
        )

    # Check if object storage has a public/presigned URL
    if storage_service.file_exists(unquoted_name):
        return RedirectResponse(url=storage_service.get_download_url(unquoted_name))

    raise HTTPException(status_code=404, detail="Requested audio track not found")

@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete an audio track from storage."""
    unquoted_name = urllib.parse.unquote(filename)

    if WORKER_URL:
        resp = proxy_to_worker("DELETE", f"/api/files/{urllib.parse.quote(unquoted_name)}")
        return resp

    if not storage_service.file_exists(unquoted_name):
        raise HTTPException(status_code=404, detail="File not found")

    storage_service.delete_file(unquoted_name)
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

    for item in storage_service.list_files():
        if f".{item.extension}" in valid_extensions:
            local_src = storage_service.get_file_path(item.filename)
            if local_src and local_src.exists():
                try:
                    dest_file = dest / item.filename
                    shutil.copy2(local_src, dest_file)
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
    """System capabilities, storage, and worker diagnostics."""
    if WORKER_URL:
        try:
            worker_info = proxy_to_worker("GET", "/api/system-info")
            return {
                "app": settings.app_name,
                "version": settings.version,
                "mode": "proxy_to_worker",
                "worker_url": WORKER_URL,
                "worker_status": "connected",
                "worker_details": worker_info,
                "sd_format_standard": "FAT32 (<=32GB recommended)"
            }
        except Exception as e:
            return {
                "app": settings.app_name,
                "version": settings.version,
                "mode": "proxy_to_worker",
                "worker_url": WORKER_URL,
                "worker_status": "disconnected",
                "worker_error": sanitize_error_message(str(e)),
                "sd_format_standard": "FAT32 (<=32GB recommended)"
            }

    files = storage_service.list_files()
    total_size = sum(f.size_bytes for f in files)

    return {
        "app": settings.app_name,
        "version": settings.version,
        "mode": "standalone_local",
        "ffmpeg_available": extractor_service.has_ffmpeg,
        "storage_backend": os.environ.get("STORAGE_BACKEND", "local"),
        "downloads_dir": str(settings.downloads_dir),
        "total_files": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "sd_format_standard": "FAT32 (<=32GB recommended)",
    }
