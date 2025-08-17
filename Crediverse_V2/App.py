# --- App.py (Crediverse_V1.1) ---
# Streamlit UI that:
#   1) Uploads PDF/DOCX
#   2) Extracts text
#   3) Sectionizes & scores
#   4) Extracts skills
#   5) Suggests track(s) from a skills map
#   6) Computes simple ATS coverage vs pasted JD
#   7) Suggests improvements

from pathlib import Path
import base64, uuid
import streamlit as st
from PIL import Image

# Local modules
from app import config  # paths / limits / dirs  :contentReference[oaicite:2]{index=2}
from app.parsing import extract_text_from_pdf, extract_text_from_docx  # text extractors  :contentReference[oaicite:3]{index=3}
from app.ai.preprocess import sectionize, tokens
from app.ai.scoring import score_resume
from app.ai.skills import extract_skills, infer_track, load_skills_map, top_tracks
from app.ai.ats import coverage
from app.ai.suggestions import suggestions

# ---------- Page config ----------
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📝", layout="wide")

# ---------- Header ----------
col1, col2 = st.columns([1, 4])
with col1:
    if config.LOGO_PATH.exists():
        st.image(Image.open(config.LOGO_PATH))
with col2:
    st.title(config.APP_NAME)
    st.caption("Phase-1 • AI-first pipeline (sectionize → score → skills → ATS)")

# ---------- Upload ----------
st.subheader("Upload your resume")
up = st.file_uploader("PDF or DOCX", type=["pdf", "docx"])
jd = st.text_area("Paste a Job Description (optional)")

if up:
    # Validate file
    ext = Path(up.name).suffix.lower()
    data = up.getvalue()
    size_mb = len(data) / 1024 / 1024

    if ext not in config.ALLOWED_EXT:
        st.error("Unsupported file type.")
        st.stop()
    if size_mb > config.MAX_FILE_MB:
        st.error(f"File is {size_mb:.1f} MB; limit {config.MAX_FILE_MB} MB.")
        st.stop()

    # Save & preview (PDF only)
    save_path = config.UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    save_path.write_bytes(data)

    if ext == ".pdf":
        with open(save_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="700" height="900"></iframe>',
            unsafe_allow_html=True,
        )

    # ---------- Extract text ----------
    if ext == ".pdf":
        resume_text = extract_text_from_pdf(str(save_path))   # :contentReference[oaicite:4]{index=4}
    else:
        resume_text = extract_text_from_docx(str(save_path))  # :contentReference[oaicite:5]{index=5}

    # ---------- AI pipeline ----------
    sections = sectionize(resume_text)          # split into logical sections
    score, score_details = score_resume(sections)
    auto_tokens = tokens(sections["__full__"])  # tokenize the full text
    auto_skills = extract_skills(auto_tokens)   # skills from tokens
    track = infer_track(auto_skills)            # legacy 1-best guess

    # ---------- Multi-track suggestion (NEW) ----------
    # Load skills map & compute top K tracks only *after* we have auto_skills
    skills_map = load_skills_map(config.BASE_DIR / "app" / "ai" / "skills_map.json")
    tracks = top_tracks(auto_skills, skills_map, k=3)  # [(track, score, matched), …]

    # Choose a best label for the metric box:
    best_track = track
    if tracks and tracks[0][1] > 0:
        best_track = tracks[0][0]
    if not best_track:
        best_track = "General Software"

    # ---------- KPIs ----------
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Resume Score", f"{score}/100")
    with c2:
        st.metric("Detected Skills", len(auto_skills))
    with c3:
        st.metric("Suggested Track", best_track)

    # ---------- Scoring details ----------
    st.subheader("Scoring Details")
    for k, present, w in score_details:
        st.write(f"- **{k.title()}**: {'✅ present' if present else '❌ missing'} (weight {w})")

    # ---------- Skills ----------
    st.subheader("Detected Skills")
    st.write(", ".join(auto_skills) if auto_skills else "—")

    # ---------- Track(s) reasoning ----------
    st.subheader("Suggested Track(s)")
    if tracks and tracks[0][1] > 0:
        for i, (t_name, t_score, matched) in enumerate(tracks, start=1):
            st.markdown(f"**{i}. {t_name}** — score {t_score}")
            if matched:
                st.caption("Matched skills: " + ", ".join(matched))
    else:
        st.info("Not enough skills detected to infer a track. Add more relevant skills.")

    # ---------- ATS coverage vs JD ----------
    if jd.strip():
        pct, present, missing = coverage(sections["__full__"], jd)
        st.subheader("ATS Coverage")
        st.write(f"**{pct}%**")
        st.caption("Present: " + (", ".join(present[:30]) or "—"))
        st.caption("Missing: " + (", ".join(missing[:30]) or "—"))
    else:
        missing = []

    # ---------- Improvement tips ----------
    st.subheader("Suggested Improvements")
    for msg in suggestions(sections, auto_skills, missing):
        st.markdown(f"- {msg}")
