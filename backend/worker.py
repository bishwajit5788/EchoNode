import os
import sys
import logging
from pathlib import Path

# Add backend directory to sys.path so modules import cleanly
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.routes import router, is_cookie_configured, is_po_token_provider_configured

logger = logging.getLogger("echonode.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

worker_app = FastAPI(
    title="EchoNode Extraction Worker",
    version=settings.version,
    description="Dedicated background extraction worker for EchoNode audio streams with FFmpeg & secure authentication."
)

@worker_app.exception_handler(HTTPException)
async def worker_http_exception_handler(request: Request, exc: HTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else exc.detail.get("error", exc.detail.get("detail", str(exc.detail)))
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": msg, "detail": msg},
        headers=exc.headers
    )

worker_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

worker_app.include_router(router)

@worker_app.get("/health")
async def health_check():
    from app.services.extractor import extractor_service
    import yt_dlp
    yt_dlp_v = "unknown"
    try:
        yt_dlp_v = getattr(yt_dlp.version, "__version__", str(getattr(yt_dlp, "__version__", "unknown")))
    except Exception:
        pass

    return {
        "status": "healthy",
        "service": "echonode-worker",
        "backend_version": settings.version,
        "version": settings.version,
        "ffmpeg_available": extractor_service.has_ffmpeg,
        "downloads_dir": str(settings.downloads_dir),
        "storage_backend": os.environ.get("STORAGE_BACKEND", "local"),
        "youtube_cookie_configured": is_cookie_configured(),
        "youtube_po_token_provider_configured": is_po_token_provider_configured(),
        "yt_dlp_version": yt_dlp_v
    }

def main():
    host = os.environ.get("WORKER_HOST", "0.0.0.0")
    port = int(os.environ.get("WORKER_PORT", "8001"))
    # In worker runtime, clear WORKER_URL if accidentally set so worker doesn't proxy to itself
    if os.environ.get("WORKER_URL"):
        os.environ["WORKER_URL"] = ""
    os.environ["EXTRACTION_MODE"] = "local"
    logger.info(f"Starting EchoNode persistent extraction worker on {host}:{port}")
    uvicorn.run(worker_app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
