# 🌐 EchoNode Ingestion Hub (FastAPI + yt-dlp)

The **EchoNode Ingestion Hub** is a dedicated web service that converts YouTube URLs into pure, video-free `.m4a` audio files formatted specifically for playback on the **EchoNode Bedside Audio Player** (Waveshare ESP32-S3-Touch-LCD-1.85).

---

## ⚡ Key Capabilities

* 🎵 **Pure Audio Containerization:** Strips all video tracks (`vide`), containerizing strictly to pure audio `.m4a` (AAC) or `.mp3`.
* 🛡️ **Container Stream Auditing:** Pure-Python ISO BMFF atom parser inspects `moov/trak/mdia/hdlr` atoms to guarantee 0 video streams exist before staging.
* 💾 **FAT32 Filename Sanitization:** Enforces FAT32 character bounds (eliminates `/\:*?"<>|`) and limits title length to $\le 60$ characters.
* 🌐 **Modern Dark-Mode Web UI:** Responsive, ambient web interface featuring clipboard paste, real-time job progress tracking, audio preview player, and MicroSD card sync.
* ☁️ **Dual Deployment Modes:** Runs natively on local development machines, homelabs, and Raspberry Pis, or as a serverless ASGI application on Vercel.

---

## 🚀 Running Locally (Recommended for Daily Ingestion)

Running locally uses your residential Internet connection, completely bypassing YouTube datacenter bot detection:

```bash
# Option 1: Via project Makefile
make run-backend

# Option 2: Directly via Python
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open your browser to:
👉 **`http://localhost:8000`**

Extracted files are staged automatically in `backend/downloads/` ready for MicroSD card transfer.

---

## ☁️ Cloud Deployment (Vercel Serverless)

The backend is fully configured for deployment on Vercel.

### Vercel Serverless Architecture & Considerations
1. **Writable Storage (`/tmp`):**
   AWS Lambda and Vercel serverless containers mount the application bundle as read-only. EchoNode automatically routes temporary download staging to `/tmp/downloads`.
2. **Synchronous Execution:**
   In serverless environments, detached background tasks are paused when HTTP responses complete. EchoNode detects serverless runtimes (`VERCEL=1`) and executes extraction synchronously within the active request lifecycle.
3. **Datacenter Bot Challenge Workaround (`YTDLP_COOKIES`):**
   YouTube challenges requests originating from major cloud datacenter IP blocks (AWS us-east-1). To run audio extraction in the cloud, export your YouTube session cookies in Netscape format (using browser extensions like "Get cookies.txt locally") and set them as an environment variable in Vercel:
   * **Key:** `YTDLP_COOKIES`
   * **Value:** `<contents of your exported cookies.txt>`

---

## 📡 API Reference

Interactive Swagger documentation is available at `/docs`, with OpenAPI JSON at `/openapi.json`.

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Ambient dark-mode web dashboard UI |
| `/health` | `GET` | Health check returning status, app name, and version |
| `/api/system-info` | `GET` | Storage stats, downloads directory, and FFmpeg detection |
| `/api/extract` | `POST` | Submits a YouTube link for pure audio extraction |
| `/api/jobs` | `GET` | Lists all active and tracked extraction jobs |
| `/api/jobs/{job_id}` | `GET` | Status, progress percentage, and error diagnosis for a job |
| `/api/files` | `GET` | Lists all staged audio tracks ready for MicroSD card transfer |
| `/api/download/{filename}` | `GET` | Streams or downloads a specific staged audio track |
| `/api/files/{filename}` | `DELETE` | Deletes a staged audio track from disk |
| `/api/sync-sd` | `POST` | Copies all staged audio files to a mounted MicroSD card path |

---

## 🧪 Testing & Validation

```bash
# Run unit tests (FAT32 sanitization & downloads directory)
python backend/tests/test_backend.py

# Run audio-only container atom security audit & URL hardening
python backend/tests/test_audio_only.py

# Run live extraction verification with public domain sample
python backend/tests/test_extraction_live.py
```
