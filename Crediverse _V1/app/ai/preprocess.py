import nltk
from nltk.data import find

def _ensure_nltk():
    try:
        find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    try:
        find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab')
    try:
        find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

_ensure_nltk()


import re, unicodedata
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

_STOP = set(stopwords.words("english"))

SECTION_PATTERNS = {
    "summary": r"(summary|objective)\b",
    "experience": r"(experience|work history)\b",
    "education": r"(education|academics)\b",
    "skills": r"\bskills?\b",
    "projects": r"\bprojects?\b",
    "achievements": r"\bachievements?\b",
}

def normalize_text(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()

def sectionize(text: str):
    text = normalize_text(text)
    lines = text.splitlines()
    out = {"__full__": text}
    current = "other"; buf = []
    def flush():
        if buf:
            out[current] = (out.get(current,"") + "\n" + "\n".join(buf)).strip()
    for ln in lines:
        low = ln.lower().strip()
        header = next((k for k,pat in SECTION_PATTERNS.items() if re.search(pat, low)), None)
        if header:
            flush(); current = header; buf = [ln]
        else:
            buf.append(ln)
    flush()
    return out

def tokens(text: str):
    toks = [w.lower() for w in word_tokenize(text or "") if w.isalpha()]
    return [w for w in toks if w not in _STOP and len(w) > 2]
