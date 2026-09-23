import re
import sqlite3
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional
from ..models import JobStatus
from ..config import settings

logger = logging.getLogger("echonode.job_store")

def sanitize_error_message(err_str: Optional[str]) -> Optional[str]:
    """
    Scrub sensitive credentials, tokens, cookies, auth headers, and host paths
    from error strings to prevent leaking them to UI, logs, or API responses.
    """
    if not err_str:
        return None

    cleaned = str(err_str)

    # 1. Redact local system user directories
    cleaned = re.sub(r'/Users/[^/\s]+', '/Users/[USER]', cleaned)
    cleaned = re.sub(r'/home/[^/\s]+', '/home/[USER]', cleaned)

    # 2. Redact Netscape cookie line entries (domain, flag, path, secure, expiry, name, value)
    cleaned = re.sub(r'(\.youtube\.com|\.google\.com|\#HttpOnly_\.youtube\.com)\s+(TRUE|FALSE)\s+[^\s]+\s+(TRUE|FALSE)\s+\d+\s+[^\s]+\s+[^\s]+', '[REDACTED_COOKIE_ENTRY]', cleaned)
    cleaned = re.sub(r'(\.youtube\.com|\.google\.com|\#HttpOnly_\.youtube\.com)\s+[^\n\r]+', '[REDACTED_COOKIE_ENTRY]', cleaned)

    # 3. Redact specific cookie and session tokens
    cleaned = re.sub(r'(SAPISID|SSID|HSID|SID|LOGIN_INFO|VISITOR_INFO1_LIVE)=[^\s;]+', r'\1=[REDACTED]', cleaned)
    cleaned = re.sub(r'(?i)(cookiefile|cookies?|auth|token|session|key)[=:\s]+["\']?[a-zA-Z0-9_\-\.\/\\+=]{8,}["\']?', r'\1=[REDACTED]', cleaned)
    cleaned = re.sub(r'Bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer [REDACTED]', cleaned)

    # 4. Trim excessively long error dumps for client readability
    if len(cleaned) > 500:
        cleaned = cleaned[:497] + "..."

    return cleaned

class JobStore:
    """
    Persistent SQLite-backed job storage.
    Survives worker restarts and serverless container lifecycles.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None

        if db_path is not None:
            self.db_path = str(db_path)
        else:
            try:
                db_dir = settings.downloads_dir
                db_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = str(db_dir / "echonode_jobs.db")
            except Exception:
                self.db_path = ":memory:"

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        with self.lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    def __del__(self):
        self.close()

    def _init_db(self):
        with self.lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        status TEXT NOT NULL,
                        progress REAL NOT NULL DEFAULT 0.0,
                        title TEXT,
                        filename TEXT,
                        download_url TEXT,
                        file_size_bytes INTEGER,
                        duration_seconds REAL,
                        error TEXT,
                        created_at REAL NOT NULL,
                        completed_at REAL
                    )
                """)
                conn.commit()
            except Exception as e:
                logger.error(f"Failed to initialize JobStore database at {self.db_path}: {e}")
                self.close()
                self.db_path = ":memory:"
                conn = self._get_connection()
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        status TEXT NOT NULL,
                        progress REAL NOT NULL DEFAULT 0.0,
                        title TEXT,
                        filename TEXT,
                        download_url TEXT,
                        file_size_bytes INTEGER,
                        duration_seconds REAL,
                        error TEXT,
                        created_at REAL NOT NULL,
                        completed_at REAL
                    )
                """)
                conn.commit()

    def create_job(self, job: JobStatus) -> None:
        with self.lock:
            conn = self._get_connection()
            conn.execute("""
                INSERT OR REPLACE INTO jobs (
                    job_id, url, status, progress, title, filename,
                    download_url, file_size_bytes, duration_seconds,
                    error, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.url,
                job.status,
                job.progress,
                job.title,
                job.filename,
                job.download_url,
                job.file_size_bytes,
                job.duration_seconds,
                sanitize_error_message(job.error),
                job.created_at,
                job.completed_at
            ))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        with self.lock:
            conn = self._get_connection()
            cur = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if not row:
                return None
            return JobStatus(
                job_id=row["job_id"],
                url=row["url"],
                status=row["status"],
                progress=row["progress"],
                title=row["title"],
                filename=row["filename"],
                download_url=row["download_url"],
                file_size_bytes=row["file_size_bytes"],
                duration_seconds=row["duration_seconds"],
                error=row["error"],
                created_at=row["created_at"],
                completed_at=row["completed_at"]
            )

    def update_job(self, job_id: str, **kwargs) -> Optional[JobStatus]:
        job = self.get_job(job_id)
        if not job:
            return None

        for k, v in kwargs.items():
            if hasattr(job, k):
                if k == "error" and v is not None:
                    setattr(job, k, sanitize_error_message(v))
                else:
                    setattr(job, k, v)

        self.create_job(job)
        return job

    def list_jobs(self) -> List[JobStatus]:
        with self.lock:
            conn = self._get_connection()
            cur = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC")
            rows = cur.fetchall()
            results = []
            for row in rows:
                results.append(JobStatus(
                    job_id=row["job_id"],
                    url=row["url"],
                    status=row["status"],
                    progress=row["progress"],
                    title=row["title"],
                    filename=row["filename"],
                    download_url=row["download_url"],
                    file_size_bytes=row["file_size_bytes"],
                    duration_seconds=row["duration_seconds"],
                    error=row["error"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"]
                ))
            return results

    def delete_job(self, job_id: str) -> bool:
        with self.lock:
            conn = self._get_connection()
            cur = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            conn.commit()
            return cur.rowcount > 0

    def clear(self) -> None:
        with self.lock:
            conn = self._get_connection()
            conn.execute("DELETE FROM jobs")
            conn.commit()

# Global default job store
job_store = JobStore()
