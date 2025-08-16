from pathlib import Path
import base64, uuid
import streamlit as st
from PIL import Image

from app import config
from app.parsing import extract_text_from_pdf, extract_text_from_docx
from app.ai.preprocess import sectionize, tokens
from app.ai.scoring import score_resume
from app.ai.skills import extract_skills, infer_track
from app.ai.ats import coverage
from app.ai.suggestions import suggestions

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📝", layout="wide")

# header
col1, col2 = st.columns([1,4])
with col1:
    if config.LOGO_PATH.exists():
        st.image(Image.open(config.LOGO_PATH))
with col2:
    st.title(config.APP_NAME)
    st.caption("Phase-1 • AI-first pipeline (sectionize → score → skills → ATS)")

# upload
st.subheader("Upload your resume")
up = st.file_uploader("PDF or DOCX", type=["pdf","docx"])
jd = st.text_area("Paste a Job Description (optional)")

if up:
    ext = Path(up.name).suffix.lower()
    data = up.getvalue()
    size_mb = len(data)/1024/1024
    if ext not in config.ALLOWED_EXT:
        st.error("Unsupported file type.")
        st.stop()
    if size_mb > config.MAX_FILE_MB:
        st.error(f"File is {size_mb:.1f} MB; limit {config.MAX_FILE_MB} MB.")
        st.stop()

    # save and preview (pdf only)
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = config.UPLOAD_DIR / save_name
    save_path.write_bytes(data)

    if ext == ".pdf":
        with open(save_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="700" height="900"></iframe>', unsafe_allow_html=True)

    # extract text
    if ext == ".pdf":
        resume_text = extract_text_from_pdf(str(save_path))
    else:
        resume_text = extract_text_from_docx(str(save_path))

    # AI pipeline
    sections = sectionize(resume_text)
    score, score_details = score_resume(sections)
    auto_tokens = tokens(sections["__full__"])
    auto_skills = extract_skills(auto_tokens)
    track = infer_track(auto_skills)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Resume Score", f"{score}/100")
    with c2:
        st.metric("Detected Skills", len(auto_skills))
    with c3:
        st.metric("Suggested Track", track)

    st.subheader("Scoring Details")
    for k, present, w in score_details:
        st.write(f"- **{k.title()}**: {'✅ present' if present else '❌ missing'} (weight {w})")

    st.subheader("Detected Skills")
    st.write(", ".join(auto_skills) if auto_skills else "—")

    if jd.strip():
        pct, present, missing = coverage(sections["__full__"], jd)
        st.subheader("ATS Coverage")
        st.write(f"**{pct}%**")
        st.caption("Present: " + (", ".join(present[:30]) or "—"))
        st.caption("Missing: " + (", ".join(missing[:30]) or "—"))
    else:
        missing = []

    st.subheader("Suggested Improvements")
    for msg in suggestions(sections, auto_skills, missing):
        st.markdown(f"- {msg}")
