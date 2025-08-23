from pathlib import Path
import uuid
import tempfile
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---- your internal modules ----
from app import config
from app.parsing import extract_text_from_pdf, extract_text_from_docx
from app.ai.preprocess import sectionize, tokens
from app.ai.scoring import score_resume
from app.ai.skills import extract_skills, infer_track, load_skills_map, top_tracks
from app.ai.ats import coverage
from app.ai.suggestions import suggestions


# ---------- response schema (for docs) ----------
class TrackItem(BaseModel):
    name: str
    score: float
    matched: List[str]

class ScoreDetail(BaseModel):
    key: str
    present: bool
    weight: float

class AnalyzeResponse(BaseModel):
    score: int
    score_details: List[ScoreDetail]
    detected_skills: List[str]
    suggested_track: str
    tracks: List[TrackItem]
    pages: int
    user_level: str
    ats: Optional[Dict[str, Any]] = None
    suggestions: List[str]
    meta: Dict[str, Any]


app = FastAPI(title="AI Resume Analyzer API", version="1.0.0")

# (optional) enable CORS for your frontend (edit origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with ["http://localhost:3000", "https://your-domain"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _temp_save(upload: UploadFile) -> Path:
    """Save UploadFile to a temp path preserving extension."""
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only .pdf or .docx allowed.")
    tmpdir = Path(tempfile.gettempdir())
    out = tmpdir / f"{uuid.uuid4().hex}{suffix}"
    with out.open("wb") as f:
        f.write(upload.file.read())
    return out


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(..., description="PDF or DOCX resume"),
    job_description: Optional[str] = Form(None, description="Optional JD text"),
):
    """
    Upload a resume (PDF/DOCX). Optionally include a Job Description.
    Returns structured JSON with score, skills, tracks, ATS, and suggestions.
    """
    # ---- validate + save ----
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or DOCX.")

    # enforce size limit using your config
    data = await file.read()
    size_mb = len(data) / 1024 / 1024
    if size_mb > config.MAX_FILE_MB:
        raise HTTPException(status_code=413, detail=f"File is {size_mb:.1f} MB; limit {config.MAX_FILE_MB} MB.")
    # we need file.read() again later; reset the stream by using saved bytes
    upload_clone = UploadFile(filename=file.filename, file=bytes_to_filelike(data))

    # save once to temp so your extractors (path-based) can work
    saved_path = _temp_save(upload_clone)

    # ---- extract text ----
    if ext == ".pdf":
        resume_text = extract_text_from_pdf(str(saved_path))
    else:
        resume_text = extract_text_from_docx(str(saved_path))

    # ---- ai pipeline ----
    sections = sectionize(resume_text)
    score, score_details_raw = score_resume(sections)
    auto_tokens = tokens(sections["__full__"])
    auto_skills = extract_skills(auto_tokens)

    # tracks
    skills_map = load_skills_map(config.BASE_DIR / "app" / "ai" / "skills_map.json")
    track_list = top_tracks(auto_skills, skills_map, k=3)  # [(track, score, matched)]
    fallback = infer_track(auto_skills)
    best_track = track_list[0][0] if (track_list and track_list[0][1] > 0) else (fallback or "General Software")

    # ats coverage (optional)
    ats_block = None
    if job_description and job_description.strip():
        pct, present, missing = coverage(sections["__full__"], job_description)
        ats_block = {
            "percent": pct,
            "present": present[:100],
            "missing": missing[:100],
        }

    pages = len(sections.get("__pages__", [])) or 1
    user_level = "Fresher" if pages == 1 else ("Intermediate" if pages == 2 else "Experienced")

    # normalize structures for response_model
    score_details = [
        {"key": k, "present": bool(present), "weight": float(w)}
        for (k, present, w) in score_details_raw
    ]
    tracks = [
        {"name": t, "score": float(sc), "matched": matched or []}
        for (t, sc, matched) in (track_list or [])
    ]

    # build response
    resp = {
        "score": int(score),
        "score_details": score_details,
        "detected_skills": auto_skills,
        "suggested_track": best_track,
        "tracks": tracks,
        "pages": int(pages),
        "user_level": user_level,
        "ats": ats_block,
        "suggestions": list(suggestions(sections, auto_skills, ats_block["missing"] if ats_block else [])),
        "meta": {
            "filename": file.filename,
            "ext": ext,
            "size_mb": round(size_mb, 3),
        },
    }
    try:
        saved_path.unlink(missing_ok=True)
    except Exception:
        pass
    return resp


# helper: recreate a file-like object from bytes (so we can save once)
from io import BytesIO
def bytes_to_filelike(b: bytes):
    bio = BytesIO(b)
    bio.seek(0)
    return bio