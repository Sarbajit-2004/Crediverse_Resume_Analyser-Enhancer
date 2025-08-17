# app/ai/assistant.py
from __future__ import annotations
import re
from typing import Dict, List, Tuple

# --------- tiny helpers (no NLTK needed) ---------
_STOP = set("""
the a an and or of in on for with to from by as at is are be this that those these
your you we our their i me my he she they them his her its was were been being
""".split())

def _tokens(text: str) -> List[str]:
    """Simple, fast tokenizer suitable for ATS-ish keyword matching."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9+\-#\.]*", (text or "").lower())
    return [w for w in words if w not in _STOP and len(w) > 2]

def _keywords(text: str) -> List[str]:
    """Unique keywords preserving order of first appearance."""
    seen = set()
    out: List[str] = []
    for w in _tokens(text):
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out

def _choose_summary(skills: List[str]) -> str:
    core = [s for s in skills if len(s) >= 3][:6]
    if not core:
        return ("Results-driven developer with a track record of shipping features, "
                "collaborating across teams, and writing clean, maintainable code.")
    tech_str = ", ".join(core[:-1]) + (f" and {core[-1]}" if len(core) > 1 else core[0])
    return (f"Results-driven engineer experienced in building reliable products with "
            f"{tech_str}. Focused on writing clean code, automating workflows, and "
            f"delivering measurable impact.")

# -------------------------------------------------

def _jd_gap(resume_text: str, jd_text: str | None) -> Dict:
    """Compare JD vs Resume keywords (lightweight ATS-style)."""
    if not jd_text:
        return {"coverage": None, "present": [], "missing": []}

    res_keys = set(_keywords(resume_text))
    jd_keys  = _keywords(jd_text)

    present = [k for k in jd_keys if k in res_keys]
    missing = [k for k in jd_keys if k not in res_keys]
    coverage = 0 if not jd_keys else round(100 * len(present) / len(jd_keys))
    return {"coverage": coverage, "present": present[:50], "missing": missing[:50]}

def generate_improvements(
    resume_text: str,
    detected_skills: List[str],
    section_presence: Dict[str, bool],
    jd_text: str | None = None
) -> Dict:
    """
    Return a dict with:
      - improved_summary: str
      - suggestions: Dict[str, List[str]]   # bullets grouped by section
      - jd_match: {coverage, present, missing}
    """
    suggestions: Dict[str, List[str]] = {
        "Summary": [],
        "Experience": [],
        "Projects": [],
        "Skills": [],
        "Education": [],
        "Achievements": [],
        "Format/ATS": []
    }

    # --- section-aware suggestions ---
    if not section_presence.get("summary", False):
        suggestions["Summary"].append("Add a 2–3 line summary with role, years of experience, core stack, and impact.")
    else:
        suggestions["Summary"].append("Tighten your summary: 2–3 lines, include role + core tech + one quantified win.")

    if not section_presence.get("experience", False):
        suggestions["Experience"].append("Add professional experience or internships with role, company, dates.")
    suggestions["Experience"].extend([
        "Use action verbs (Built, Led, Automated, Delivered) and quantify impact (e.g., reduced latency by 30%).",
        "Follow the STAR format: Situation → Task → Action → Result; 3–5 bullets per role."
    ])

    if not section_presence.get("projects", False):
        suggestions["Projects"].append("Add 2–3 projects with one-line problem, your contribution, tech used, and outcome.")
    suggestions["Projects"].append("Link to code/demo where possible; list tools per project (React, Django, Docker, etc.).")

    if not section_presence.get("skills", False):
        suggestions["Skills"].append("Add a Skills section grouped by category (Languages, Frameworks, Tools, Cloud).")
    suggestions["Skills"].append("Prioritize skills relevant to the target role; keep the list curated (8–15 items).")

    if not section_presence.get("education", False):
        suggestions["Education"].append("Add Education with degree, institution, year (and GPA if strong).")

    if not section_presence.get("achievements", False):
        suggestions["Achievements"].append("Add 2–3 achievements: awards, publications, certifications, hackathons.")
    suggestions["Achievements"].append("Prefer measurable achievements (KPIs, rankings, users, revenue, costs saved).")

    # --- formatting / ATS hygiene ---
    suggestions["Format/ATS"].extend([
        "Export as PDF, single column, standard fonts; avoid tables/text boxes that may break ATS parsing.",
        "Keep to 1 page (fresher) or 2 pages (experienced); consistent headings and spacing.",
        "Use consistent tense (present for current role, past for previous roles); avoid first-person pronouns."
    ])

    # --- improved summary (synthetic) ---
    base_summary = _choose_summary(detected_skills)

    # --- JD match (optional) ---
    jd_match = _jd_gap(resume_text, jd_text)

    return {
        "improved_summary": base_summary,
        "suggestions": suggestions,
        "jd_match": jd_match
    }
