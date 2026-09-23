from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import settings
from .api.routes import router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Bedside Audio Device Ingestion Web Service - Extracts video-free M4A audio streams for ESP32-S3 playback."
)

# Enable CORS for local cross-origin development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(router)

# Serve static web dashboard
if settings.static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = settings.static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "EchoNode Backend is running. Visit /docs for Swagger API documentation."}

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.version}
