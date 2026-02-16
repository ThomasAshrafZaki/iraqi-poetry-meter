import re

_AR_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا",
    "ة": "ه", "ى": "ي",
    "ؤ": "و", "ئ": "ي",
})

def normalize(text: str) -> str:
    t = text.strip().translate(_AR_MAP)
    # remove tatweel and extra punctuation
    t = t.replace("ـ", " ")
    t = re.sub(r"[^\u0600-\u06FF\s\.]", " ", t)  # keep Arabic + spaces + dot
    t = re.sub(r"\s+", " ", t).strip()
    return t