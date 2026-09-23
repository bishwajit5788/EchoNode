from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from .config import settings
from .api.routes import router, get_worker_url, check_worker_health

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Bedside Audio Device Ingestion Web Service - Extracts video-free M4A audio streams for ESP32-S3 playback."
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else exc.detail.get("error", exc.detail.get("detail", str(exc.detail)))
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": msg, "detail": msg},
        headers=exc.headers
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
    worker_url = get_worker_url()
    worker_configured = bool(worker_url)
    reachable = None
    if worker_configured:
        reachable, _ = check_worker_health(timeout=2.0)

    mode = "proxy_to_worker" if worker_configured else "standalone_local"

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "mode": mode,
        "worker_configured": worker_configured,
        "worker_reachable": reachable
    }
