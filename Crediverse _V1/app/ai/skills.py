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
