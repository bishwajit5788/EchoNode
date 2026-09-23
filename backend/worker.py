import os
import sys
import logging
from pathlib import Path

# Add backend directory to sys.path so modules import cleanly
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router

logger = logging.getLogger("echonode.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

worker_app = FastAPI(
    title="EchoNode Extraction Worker",
    version=settings.version,
    description="Dedicated background extraction worker for EchoNode audio streams with FFmpeg & secure authentication."
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
    return {
        "status": "healthy",
        "service": "echonode-worker",
        "ffmpeg_available": extractor_service.has_ffmpeg,
        "downloads_dir": str(settings.downloads_dir)
    }

def main():
    host = os.environ.get("WORKER_HOST", "0.0.0.0")
    port = int(os.environ.get("WORKER_PORT", "8001"))
    logger.info(f"Starting EchoNode persistent extraction worker on {host}:{port}")
    uvicorn.run(worker_app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
