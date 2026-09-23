# 🌐 EchoNode Ingestion Hub & Extraction Engine

The **EchoNode Ingestion Hub** converts YouTube URLs into pure, video-free `.m4a` (AAC-LC) audio streams tailored specifically for hardware decoding on the **EchoNode Bedside Audio Player** (Waveshare ESP32-S3-Touch-LCD-1.85 with PCM5101 I2S DAC).

---

## 🏛️ Production 3-Tier Architecture

To overcome cloud datacenter bot challenges and serverless compute/filesystem constraints, EchoNode uses a decoupled 3-tier production architecture:

```
Vercel Edge / Serverless
  ├── Web UI (Ambient Glassmorphism Dashboard)
  ├── Lightweight API Proxy / Coordinator
  └── Immediate Job Submission & Status Polling

Persistent Extraction Worker (Docker / VPS / Local Server)
  ├── yt-dlp Ingestion Engine
  ├── FFmpeg Transcoding Pipeline (~128 kbps AAC-LC)
  ├── Secure YouTube Access (YTDLP_COOKIES & PO-Token Support)
  └── Pure-Python ISO BMFF Container Verification (0 video tracks)

Persistent Storage Layer
  ├── SQLite Durable JobStore (echonode_jobs.db surviving reboots)
  └── Pluggable Storage (Local filesystem or S3 / Cloudflare R2 / MinIO)
```

---

## ⚡ Key Capabilities

* 🎵 **Pure Audio Containerization:** Strips all video tracks (`vide`), containerizing strictly to pure audio `.m4a` (AAC-LC) or `.mp3`.
* 🛡️ **Container Stream Auditing:** Pure-Python ISO BMFF atom parser inspects `moov/trak/mdia/hdlr` atoms to guarantee 0 video streams exist before staging.
* 💾 **FAT32 Filename Sanitization:** Enforces FAT32 character bounds (eliminates `/\:*?"<>|`) and limits title length to $\le 60$ characters.
* 🔒 **Zero-Secret Leakage Guarantee:** Credentials, cookie contents, session IDs, and tokens are scrubbed automatically from all error strings, API payloads, and log outputs.
* 📦 **Persistent Job State:** SQLite ACID storage preserves job history, states (`queued`, `processing`, `completed`, `failed`), and progress across process and container recycles.
* 🎛️ **Dual-Mode Operation:** Works out-of-the-box as a standalone local server or as a cloud proxy pointing to a persistent worker.

---

## 🚀 Running Locally (Standalone Mode)

Local execution uses your residential or office ISP connection, which is not flagged by YouTube datacenter IP reputation filters:

```bash
# Start standalone local ingestion server (UI + API + Worker on http://localhost:8000)
make run-backend
```

Open your browser to:
👉 **`http://localhost:8000`**

Extracted files are staged automatically in `backend/downloads/` ready for direct MicroSD card synchronization.

---

## ⚙️ Running the Dedicated Worker

For persistent cloud deployments (Vercel frontend + dedicated worker):

```bash
# Set environment secrets (optional for datacenter IPs)
export YTDLP_COOKIES="<contents of exported cookies.txt>"
export PORT=8001

# Start worker service
make run-worker
# Or: python backend/worker.py
```

### Configuring Vercel to use the Persistent Worker

In the Vercel Project Dashboard -> **Settings** -> **Environment Variables**:
* **`WORKER_URL`**: `https://your-worker-domain.com` (e.g. deployed on Fly.io, Railway, VPS, or tunnel)

When `WORKER_URL` is set, Vercel acts as a lightweight proxy, instantly forwarding extraction requests and status queries to your worker.

---

## 🔒 Secure YouTube Authentication Configuration

YouTube's BotGuard restricts unauthenticated access from major cloud datacenter IP ranges (AWS, GCP, Azure, Oracle).

### Supported Secure Authentication Methods

1. **`YTDLP_COOKIES` (Environment Variable)**:
   Export your YouTube cookies in Netscape format (using browser extensions such as *Get cookies.txt locally* in an incognito window).
   Set the content as a server-side secret environment variable:
   ```bash
   YTDLP_COOKIES="# Netscape HTTP Cookie File\n# ..."
   ```
   *Security Note: The worker writes cookies to a temporary file with strict `0600` permissions and automatically shreds/deletes it upon job completion.*

2. **`YTDLP_COOKIES_PATH` (File Path)**:
   Point to a secure, gitignored file on the server filesystem:
   ```bash
   YTDLP_COOKIES_PATH=/etc/echonode/cookies.txt
   ```

3. **Cookie Rotation Guidelines**:
   - YouTube session cookies typically remain valid for several weeks to months.
   - When a session expires, export fresh cookies from your browser and update the environment secret.
   - **NEVER** commit cookie files to version control (`.gitignore` enforces this).
   - **NEVER** expose cookies to frontend JavaScript.

---

## 📡 API Reference

Interactive Swagger documentation is available at `/docs`, with OpenAPI JSON at `/openapi.json`.

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Ambient dark-mode web dashboard UI |
| `/health` | `GET` | Health check returning status, app name, and version |
| `/api/system-info` | `GET` | Storage stats, worker mode, downloads directory, and FFmpeg detection |
| `/api/extract` | `POST` | Submits a YouTube link for pure audio extraction |
| `/api/jobs` | `GET` | Lists all active and completed extraction jobs |
| `/api/jobs/{job_id}` | `GET` | Status (`queued`, `processing`, `completed`, `failed`), progress %, and sanitized error diagnosis |
| `/api/files` | `GET` | Lists all staged audio tracks ready for MicroSD card transfer |
| `/api/download/{filename}` | `GET` | Streams or downloads a specific staged audio track |
| `/api/files/{filename}` | `DELETE` | Deletes a staged audio track from disk/storage |
| `/api/sync-sd` | `POST` | Copies all staged audio files to a mounted MicroSD card path |

---

## 🧪 Testing & Verification

```bash
# Run all backend unit and architecture tests:
make test-backend

# Individual test suites:
python backend/tests/test_job_store.py              # SQLite persistence & error sanitization
python backend/tests/test_storage.py                # Local & S3 storage adapters
python backend/tests/test_backend.py                # Route validation & error handling
python backend/tests/test_audio_only.py             # ISO BMFF pure audio stream validation
python backend/tests/test_phase7_verification.py   # Comprehensive Phase 7 pipeline validation
```
