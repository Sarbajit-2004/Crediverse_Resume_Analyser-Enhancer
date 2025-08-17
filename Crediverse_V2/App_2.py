# App.py — User + Admin (pymysql-only)
# ------------------------------------
# Phase-1 AI flow + Admin panel. No SQLAlchemy required.

from pathlib import Path
import base64, uuid, datetime as dt
import pandas as pd
import streamlit as st
from PIL import Image

# ---- Internal modules (yours) ----
from app import config
from app.parsing import extract_text_from_pdf, extract_text_from_docx
from app.ai.preprocess import sectionize, tokens
from app.ai.scoring import score_resume
from app.ai.skills import extract_skills, infer_track, load_skills_map, top_tracks
from app.ai.ats import coverage
from app.ai.suggestions import suggestions

# ---- DB + charts ----
import pymysql
import plotly.express as px

# ---------- Page setup ----------
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📝", layout="wide")

# ---------- Small helpers ----------
def show_pdf(path: Path):
    """Inline preview for PDFs only."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" width="700" height="900"></iframe>',
        unsafe_allow_html=True,
    )

def mysql_cfg():
    """Fetch MySQL secrets; return {} if missing."""
    return st.secrets.get("mysql", {})

def get_db_conn(db_required=True):
    """
    Return a pymysql connection using st.secrets['mysql'].
    If db_required=True, connect to that database; otherwise connect to server only.
    """
    cfg = mysql_cfg()
    if not cfg:
        raise RuntimeError("MySQL credentials not found in .streamlit/secrets.toml")
    host = cfg.get("host", "localhost")
    user = cfg.get("user", "root")
    password = cfg.get("password", "")
    db = cfg.get("db", "cv")
    if db_required:
        return pymysql.connect(host=host, user=user, password=password, database=db, autocommit=True)
    return pymysql.connect(host=host, user=user, password=password, autocommit=True)

def init_db():
    """Create DB and table if missing. Safe to call on every startup."""
    try:
        # Create DB if missing
        conn = get_db_conn(db_required=False)
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS cv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()

        # Create table if missing
        conn = get_db_conn(db_required=True)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_data(
                    ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    Name VARCHAR(200),
                    Email_ID VARCHAR(200),
                    Resume_Score INT,
                    Timestamp VARCHAR(50),
                    Page_no INT,
                    Predicted_Field VARCHAR(100),
                    User_level VARCHAR(50),
                    Actual_skills TEXT,
                    Recommended_skills TEXT,
                    Recommended_courses TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        conn.close()
        return True, "Database ready."
    except Exception as e:
        return False, f"DB init failed: {e}"

def insert_row(name, email, score, pages, reco_field, user_level, skills, rec_skills, courses):
    """Insert one analysis row; returns True/False."""
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_data
                (Name, Email_ID, Resume_Score, Timestamp, Page_no, Predicted_Field, User_level,
                 Actual_skills, Recommended_skills, Recommended_courses)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    name or "",
                    email or "",
                    int(score),
                    dt.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
                    int(pages or 0),
                    reco_field or "",
                    user_level or "",
                    skills or "",
                    rec_skills or "",
                    courses or "",
                ),
            )
        conn.close()
        return True
    except Exception:
        return False

def admin_creds():
    """Admin username/password from secrets with sensible defaults."""
    sec = st.secrets.get("admin", {})
    return sec.get("username", "admin"), sec.get("password", "admin123")

# ---------- Header ----------
col1, col2 = st.columns([1, 4])
with col1:
    if config.LOGO_PATH.exists():
        st.image(Image.open(config.LOGO_PATH))
with col2:
    st.title(config.APP_NAME)
    st.caption("Phase-1 • AI-first pipeline (sectionize → score → skills → ATS) + Admin")

# ---------- Sidebar mode ----------
mode = st.sidebar.radio("Choose mode", ["User", "Admin"])
st.sidebar.markdown('[©Developed by Sarbajit](https://www.linkedin.com/public-profile/settings?trk=d_flagship3_profile_self_view_public_profile)', unsafe_allow_html=True)

# ======================================================================================
#                                        USER
# ======================================================================================
if mode == "User":
    st.subheader("Upload your resume")
    up = st.file_uploader("PDF or DOCX", type=["pdf", "docx"])
    jd = st.text_area("Paste a Job Description (optional)")

    if up:
        # ---- File validation ----
        ext = Path(up.name).suffix.lower()
        data = up.getvalue()
        size_mb = len(data) / 1024 / 1024
        if ext not in config.ALLOWED_EXT:
            st.error("Unsupported file type.")
            st.stop()
        if size_mb > config.MAX_FILE_MB:
            st.error(f"File is {size_mb:.1f} MB; limit {config.MAX_FILE_MB} MB.")
            st.stop()

        # ---- Save + preview (pdf only) ----
        save_name = f"{uuid.uuid4().hex}{ext}"
        save_path = config.UPLOAD_DIR / save_name
        save_path.write_bytes(data)
        if ext == ".pdf":
            show_pdf(save_path)

        # ---- Extract text ----
        if ext == ".pdf":
            resume_text = extract_text_from_pdf(str(save_path))
        else:
            resume_text = extract_text_from_docx(str(save_path))

        # ---- AI pipeline ----
        sections = sectionize(resume_text)
        score, score_details = score_resume(sections)
        auto_tokens = tokens(sections["__full__"])
        auto_skills = extract_skills(auto_tokens)

        # Map-driven multi-track suggestion
        skills_map = load_skills_map(config.BASE_DIR / "app" / "ai" / "skills_map.json")
        tracks = top_tracks(auto_skills, skills_map, k=3)  # [(track, score, matched)]
        # fallback if empty
        _fallback = infer_track(auto_skills)
        best_track = tracks[0][0] if (tracks and tracks[0][1] > 0) else (_fallback or "General Software")

        # ---- KPI row ----
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Resume Score", f"{score}/100")
        with c2:
            st.metric("Detected Skills", len(auto_skills))
        with c3:
            st.metric("Suggested Track", best_track)

        # ---- Details ----
        st.subheader("Scoring Details")
        for k, present, w in score_details:
            st.write(f"- **{k.title()}**: {'✅ present' if present else '❌ missing'} (weight {w})")

        st.subheader("Detected Skills")
        st.write(", ".join(auto_skills) if auto_skills else "—")

        st.subheader("Suggested Track(s)")
        if tracks and tracks[0][1] > 0:
            for i, (track_name, sc, matched) in enumerate(tracks, start=1):
                st.markdown(f"**{i}. {track_name}** — score {sc}")
                if matched:
                    st.caption("Matched skills: " + ", ".join(matched))
        else:
            st.info("Not enough skills detected to infer a track. Add more relevant skills.")

        # ---- ATS coverage ----
        if jd.strip():
            pct, present, missing = coverage(sections["__full__"], jd)
            st.subheader("ATS Coverage")
            st.write(f"**{pct}%**")
            st.caption("Present: " + (", ".join(present[:30]) or "—"))
            st.caption("Missing: " + (", ".join(missing[:30]) or "—"))
        else:
            missing = []

        # ---- Suggestions ----
        st.subheader("Suggested Improvements")
        for msg in suggestions(sections, auto_skills, missing):
            st.markdown(f"- {msg}")

        # ---- Store to DB (best effort) ----
        pages = len(sections.get("__pages__", [])) or 1
        user_level = "Fresher" if pages == 1 else ("Intermediate" if pages == 2 else "Experienced")
        skills_csv = ", ".join(auto_skills)
        rec_skills = ""    # hook up to your rules if/when you add them
        rec_courses = ""   # idem

        ok = insert_row(
            name=sections.get("__name__", ""),  # add your name extractor if available
            email="",                            # add your email extractor if available
            score=score,
            pages=pages,
            reco_field=best_track,
            user_level=user_level,
            skills=skills_csv,
            rec_skills=rec_skills,
            courses=rec_courses,
        )
        if ok:
            st.success("Saved summary to the database (if configured).")
        else:
            st.info("Skipped DB write (missing or unreachable DB).")

# ======================================================================================
#                                        ADMIN
# ======================================================================================
else:
    st.subheader("Admin Login")
    a_user, a_pass = admin_creds()
    in_user = st.text_input("Username", value="", key="admin_user")
    in_pass = st.text_input("Password", value="", type="password", key="admin_pass")
    login = st.button("Login")

    if "ADMIN_OK" not in st.session_state:
        st.session_state.ADMIN_OK = False

    if login:
        st.session_state.ADMIN_OK = (in_user == a_user and in_pass == a_pass)
        if not st.session_state.ADMIN_OK:
            st.error("Invalid credentials.")

    if not st.session_state.ADMIN_OK:
        st.stop()

    # ---- DB readiness ----
    ok, msg = init_db()
    if ok:
        st.success(msg)
    else:
        st.error(msg)

    # ---- Admin tabs ----
    tab_dash, tab_records, tab_uploads, tab_settings = st.tabs(
        ["📊 Dashboard", "📑 Records", "🗂️ Uploads", "⚙️ Settings"]
    )

    # ---------------------- Dashboard ----------------------
    with tab_dash:
        try:
            conn = get_db_conn()
            df = pd.read_sql("SELECT * FROM user_data ORDER BY ID DESC", conn)
            conn.close()
        except Exception as e:
            df = pd.DataFrame()
            st.error(f"DB read failed: {e}")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Records", len(df))
        with c2:
            st.metric("Unique Emails", df["Email_ID"].nunique() if not df.empty else 0)
        with c3:
            st.metric("Avg Score", round(df["Resume_Score"].mean(), 1) if not df.empty else 0)

        if df.empty:
            st.info("No data yet.")
        else:
            st.write("Latest 20:")
            st.dataframe(df.head(20), use_container_width=True)

            left, right = st.columns(2)
            with left:
                if "Predicted_Field" in df:
                    fig1 = px.pie(df, names="Predicted_Field", title="Predicted Field Distribution")
                    st.plotly_chart(fig1, use_container_width=True)
            with right:
                if "User_level" in df:
                    fig2 = px.pie(df, names="User_level", title="User Level")
                    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------- Records ----------------------
    with tab_records:
        st.write("Browse & manage user_data")

        # Filters
        q = st.text_input("Search (name/email/field contains)")
        date_from = st.date_input("From", value=None)
        date_to = st.date_input("To", value=None)

        # Query
        where = []
        params = []
        if q:
            where.append("(Name LIKE %s OR Email_ID LIKE %s OR Predicted_Field LIKE %s)")
            like = f"%{q}%"
            params += [like, like, like]
        if date_from:
            where.append("Timestamp >= %s")
            params.append(str(date_from))
        if date_to:
            where.append("Timestamp <= %s")
            params.append(str(date_to) + " 23:59:59")

        sql = "SELECT * FROM user_data"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY ID DESC"

        try:
            conn = get_db_conn()
            df = pd.read_sql(sql, conn, params=params)
            conn.close()
        except Exception as e:
            df = pd.DataFrame()
            st.error(f"DB read failed: {e}")

        st.dataframe(df, use_container_width=True, height=400)

        # CSV export
        if not df.empty:
            csv = df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv, "user_data.csv", "text/csv")

        # Delete by ID
        del_id = st.number_input("Delete record by ID", min_value=1, step=1)
        if st.button("Delete"):
            try:
                conn = get_db_conn()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM user_data WHERE ID=%s", (int(del_id),))
                    conn.commit()
                conn.close()
                st.success(f"Deleted ID {del_id}. Refresh the page to see changes.")
            except Exception as e:
                st.error(f"Delete failed: {e}")

    # ---------------------- Uploads ----------------------
    with tab_uploads:
        st.write("Files in your upload folder")
        up_dir = config.UPLOAD_DIR
        files = sorted([p for p in up_dir.glob("*") if p.is_file()],
                       key=lambda x: x.stat().st_mtime, reverse=True)
        if not files:
            st.info("No files yet.")
        else:
            for p in files[:50]:
                st.write(f"{p.name} — {round(p.stat().st_size/1024, 1)} KB — "
                         f"{dt.datetime.fromtimestamp(p.stat().st_mtime)}")

    # ---------------------- Settings ----------------------
    with tab_settings:
        st.write("**Admin credentials (from secrets.toml)**")
        st.code(f"username = {a_user}\npassword = {a_pass}", language="bash")

        st.write("**MySQL connection (from secrets.toml)**")
        cfg = mysql_cfg()
        if isinstance(cfg, dict):
        # Only show safe keys, never passwords in plain UI
            safe = {k: v for k, v in cfg.items() if k.lower() != "password"}
            st.json(safe)
        else:
        # Show a clear message instead of trying to dump non-JSON objects
            st.warning("Your mysql block is not a valid mapping (dict). "
                   "Please check .streamlit/secrets.toml.")
            st.code(str(cfg))
