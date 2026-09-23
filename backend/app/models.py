from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field

class ExtractionRequest(BaseModel):
    url: str = Field(..., description="YouTube URL to extract audio from")
    format_preference: Optional[str] = Field("m4a", description="Target audio format ('m4a' or 'mp3')")
    custom_title: Optional[str] = Field(None, description="Optional custom filename override")

class JobStatus(BaseModel):
    job_id: str
    url: str
    status: str = Field(..., description="'queued' | 'processing' | 'downloading' | 'completed' | 'failed'")
    progress: float = 0.0
    title: Optional[str] = None
    filename: Optional[str] = None
    download_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    created_at: float
    completed_at: Optional[float] = None

class AudioFileItem(BaseModel):
    filename: str
    title: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    extension: str
    download_url: str
    sd_ready: bool = True
    created_at: float

class ExtractionResponse(BaseModel):
    job_id: str
    message: str
    status: str

class SyncRequest(BaseModel):
    target_path: str = Field(..., description="Target MicroSD mount path (e.g. /Volumes/ECHONODE)")

class SyncResponse(BaseModel):
    copied_count: int
    failed_count: int
    target_path: str
    message: str
