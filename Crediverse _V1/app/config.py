from __future__ import annotations
from pathlib import Path
import os

APP_NAME = os.getenv("APP_NAME", "AI Resume Analyser")
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = (BASE_DIR / "Uploaded_Resumes").resolve()
LOGO_PATH = (BASE_DIR / "Logo" / "Crediverse_ResumeAnalyzer.png").resolve()
LOGS_DIR = (BASE_DIR / "logs").resolve()

MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "10"))
ALLOWED_EXT = {".pdf", ".docx"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
