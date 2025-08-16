from rapidfuzz import fuzz, process
from .preprocess import tokens

def coverage(resume_text: str, jd_text: str, min_score=90):
    r = set(tokens(resume_text))
    j = set(tokens(jd_text))
    present, missing = [], []
    for term in j:
        if term in r:
            present.append(term); continue
        match = process.extractOne(term, r, scorer=fuzz.ratio)
        if match and match[1] >= min_score:
            present.append(term)
        else:
            missing.append(term)
    pct = 0 if not j else round(100 * len(present) / len(j))
    return pct, sorted(present), sorted(missing)
