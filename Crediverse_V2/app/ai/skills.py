from rapidfuzz import process, fuzz

SKILL_BANK = {
    "programming": ["python","java","c++","javascript","typescript","sql","bash","powershell"],
    "data": ["pandas","numpy","scikit-learn","tensorflow","pytorch","matplotlib","seaborn","statistics","eda","ml","nlp","computer vision","xgboost","lightgbm"],
    "web": ["react","node","django","flask","fastapi","laravel","wordpress","tailwind","next.js"],
    "mobile": ["android","kotlin","flutter","swift","xcode"],
    "cloud": ["aws","gcp","azure","docker","kubernetes","git","linux","ci/cd"],
    "uiux": ["figma","adobe xd","wireframing","prototyping","usability testing"],
}
CANON = sorted({s for lst in SKILL_BANK.values() for s in lst})

def extract_skills(tokens, min_score=90):
    found = set()
    low = set(tokens)
    for s in CANON:
        if s in low:
            found.add(s)
        else:
            match = process.extractOne(s, low, scorer=fuzz.ratio)
            if match and match[1] >= min_score:
                found.add(s)
    return sorted(found)

def infer_track(skills):
    if any(s in skills for s in ["tensorflow","pytorch","scikit-learn","ml"]): return "Data Science / ML"
    if any(s in skills for s in ["react","django","flask","node"]):           return "Web Development"
    if any(s in skills for s in ["android","kotlin","flutter","swift"]):      return "Mobile"
    if any(s in skills for s in ["figma","wireframing","prototyping"]):       return "UI/UX"
    return "General Software"

# --- Track scoring (map-driven) ---
from pathlib import Path
import json

def load_skills_map(path: str | Path) -> dict:
    """Load a skills→track map from JSON; if not found, return a safe default."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # fallback minimal map
        return {
            "Web Development": ["react","node","django","flask","javascript","html","css","nextjs"],
            "Data Science": ["pandas","numpy","scikit-learn","matplotlib","seaborn","sql"],
            "AI/ML": ["tensorflow","pytorch","nlp","cv","llm","transformers"],
            "Cloud/DevOps": ["aws","gcp","azure","docker","kubernetes","terraform"],
            "Mobile": ["android","kotlin","flutter","swift"],
            "UI/UX": ["figma","wireframing","prototyping"]
        }

def score_tracks(detected_skills: list[str], skills_map: dict) -> list[tuple[str, int, list[str]]]:
    """
    Return list of (track, score, matched_skills) sorted by score desc.
    Score = number of overlaps between detected_skills and track's canonical list.
    """
    low = {s.lower() for s in detected_skills}
    scored: list[tuple[str,int,list[str]]] = []
    for track, canon in skills_map.items():
        canon_low = [c.lower() for c in canon]
        matched = sorted(low.intersection(canon_low))
        scored.append((track, len(matched), matched))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

def top_tracks(detected_skills: list[str], skills_map: dict, k: int = 3) -> list[tuple[str, int, list[str]]]:
    return score_tracks(detected_skills, skills_map)[:k]
from typing import List, Dict
from collections import defaultdict
import re
