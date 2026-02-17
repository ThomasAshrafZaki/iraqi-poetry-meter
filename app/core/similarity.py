"""
مقاييس تشابه متقدمة مع تطبيق TF-IDF فعلي.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import List, Set, Dict, Tuple, Optional
from difflib import SequenceMatcher

from app.core.normalize import normalize_arabic, tokenize, char_ngrams, word_ngrams

# -------------------------------------------------------------
# 1. مقاييس المسافة الأساسية
# -------------------------------------------------------------

def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def levenshtein_ratio(s1: str, s2: str) -> float:
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (dist / max_len)

def jaccard_similarity(set1: Set, set2: Set) -> float:
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    inter = len(set1 & set2)
    union = len(set1 | set2)
    return inter / union if union else 0.0

def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    common = set(vec1.keys()) & set(vec2.keys())
    if not common:
        return 0.0
    dot = sum(vec1[k] * vec2[k] for k in common)
    mag1 = math.sqrt(sum(v*v for v in vec1.values()))
    mag2 = math.sqrt(sum(v*v for v in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

# -------------------------------------------------------------
# 2. مقاييس تشابه للنصوص
# -------------------------------------------------------------

def word_jaccard(text1: str, text2: str) -> float:
    return jaccard_similarity(set(tokenize(text1)), set(tokenize(text2)))

def char_ngram_jaccard(text1: str, text2: str, n: int = 3) -> float:
    return jaccard_similarity(char_ngrams(text1, n), char_ngrams(text2, n))

def word_ngram_jaccard(text1: str, text2: str, n: int = 2) -> float:
    return jaccard_similarity(word_ngrams(text1, n), word_ngrams(text2, n))

def sequence_matcher_ratio(text1: str, text2: str) -> float:
    return SequenceMatcher(None, text1, text2).ratio()

# -------------------------------------------------------------
# 3. تشابه عروضي تقريبي (اختياري)
# -------------------------------------------------------------

def simple_syllabic_pattern(text: str) -> List[int]:
    """نمط بسيط: كل حرف علة (ا و ي) يبدأ مقطعاً."""
    t = normalize_arabic(text, deep=False)
    vowels = set('اوي')
    pattern = []
    count = 0
    for ch in t:
        count += 1
        if ch in vowels:
            pattern.append(count)
            count = 0
    if count > 0:
        pattern.append(count)
    return pattern

def dtw_distance(seq1: List[int], seq2: List[int]) -> float:
    if not seq1 or not seq2:
        return float('inf')
    m, n = len(seq1), len(seq2)
    dtw = [[0.0]*(n+1) for _ in range(m+1)]
    for i in range(m+1):
        dtw[i][0] = float('inf')
    for j in range(n+1):
        dtw[0][j] = float('inf')
    dtw[0][0] = 0
    for i in range(1, m+1):
        for j in range(1, n+1):
            cost = abs(seq1[i-1] - seq2[j-1])
            dtw[i][j] = cost + min(dtw[i-1][j], dtw[i][j-1], dtw[i-1][j-1])
    return dtw[m][n] / max(m, n)

def syllabic_similarity(text1: str, text2: str) -> float:
    p1 = simple_syllabic_pattern(text1)
    p2 = simple_syllabic_pattern(text2)
    if not p1 and not p2:
        return 1.0
    if not p1 or not p2:
        return 0.0
    dist = dtw_distance(p1, p2)
    return 1.0 / (1.0 + dist)

# -------------------------------------------------------------
# 4. TF-IDF Vectorizer حقيقي
# -------------------------------------------------------------

class TfidfVectorizer:
    def __init__(self, corpus: List[str]):
        self.corpus = corpus
        self.doc_count = len(corpus)
        self.idf = self._compute_idf()

    def _compute_idf(self):
        idf = defaultdict(float)
        for doc in self.corpus:
            words = set(tokenize(doc))
            for w in words:
                idf[w] += 1.0
        for w in idf:
            idf[w] = math.log(self.doc_count / (1.0 + idf[w])) + 1.0
        return dict(idf)

    def tf(self, text: str) -> Dict[str, float]:
        words = tokenize(text)
        total = len(words)
        if total == 0:
            return {}
        cnt = Counter(words)
        return {w: c/total for w, c in cnt.items()}

    def vector(self, text: str) -> Dict[str, float]:
        tf = self.tf(text)
        vec = {}
        for w, tfv in tf.items():
            if w in self.idf:
                vec[w] = tfv * self.idf[w]
        return vec

    def similarity(self, text: str, profile_text: str) -> float:
        """تشابه بين نص ونص آخر (يمكن أن يكون profile لوزن)."""
        v1 = self.vector(text)
        v2 = self.vector(profile_text)
        return cosine_similarity(v1, v2)

# -------------------------------------------------------------
# 5. دمج المقاييس
# -------------------------------------------------------------

def combined_similarity(
    text1: str,
    text2: str,
    use_lev: bool = True,
    use_jaccard_words: bool = True,
    use_jaccard_char3: bool = True,
    use_jaccard_word2: bool = True,
    use_sequence: bool = True,
    use_syllabic: bool = False,  # افتراضياً False لأنها تقريبية
    weights: Optional[Dict[str, float]] = None
) -> float:
    if weights is None:
        weights = {
            'levenshtein': 0.25,
            'jaccard_words': 0.15,
            'jaccard_char3': 0.20,
            'jaccard_word2': 0.15,
            'sequence': 0.15,
            'syllabic': 0.10,
        }
    sims = {}
    if use_lev:
        sims['levenshtein'] = levenshtein_ratio(text1, text2)
    if use_jaccard_words:
        sims['jaccard_words'] = word_jaccard(text1, text2)
    if use_jaccard_char3:
        sims['jaccard_char3'] = char_ngram_jaccard(text1, text2, 3)
    if use_jaccard_word2:
        sims['jaccard_word2'] = word_ngram_jaccard(text1, text2, 2)
    if use_sequence:
        sims['sequence'] = sequence_matcher_ratio(text1, text2)
    if use_syllabic:
        sims['syllabic'] = syllabic_similarity(text1, text2)

    total_weight = 0.0
    result = 0.0
    for key, val in sims.items():
        w = weights.get(key, 0.0)
        result += val * w
        total_weight += w

    return result / total_weight if total_weight > 0 else 0.0

# -------------------------------------------------------------
# 6. البحث عن أفضل تطابق
# -------------------------------------------------------------

class BestMatch:
    def __init__(self, score: float, example: str, weight: str, method: str):
        self.score = score
        self.example = example
        self.weight = weight
        self.method = method

def find_best_match(
    text: str,
    candidates: List[Tuple[str, str]],
    weight_profiles: Optional[Dict[str, str]] = None,
    vectorizer: Optional[TfidfVectorizer] = None
) -> BestMatch:
    """
    candidates: (weight_name, example_text)
    weight_profiles: name -> combined_text (لمقارنة TF-IDF)
    vectorizer: كائن TfidfVectorizer مدرب على كل الأمثلة
    """
    best = BestMatch(score=0.0, example="", weight="", method="")

    # 1. مقارنة مع كل مثال مباشرة
    for w, ex in candidates:
        sim = combined_similarity(text, ex)
        if sim > best.score:
            best.score = sim
            best.example = ex
            best.weight = w
            best.method = "example_similarity"

    # 2. إذا كان لدينا weight_profiles و vectorizer، نقارن مع ملف كل وزن
    if weight_profiles and vectorizer and best.score < 0.9:
        for w, profile in weight_profiles.items():
            sim = vectorizer.similarity(text, profile)
            # نعطي وزنًا إضافيًا للمقارنة على مستوى الوزن
            if sim * 1.1 > best.score:
                best.score = sim * 1.1
                # نختار أول مثال لهذا الوزن كمرجع
                first_ex = next((ex for (wei, ex) in candidates if wei == w), "")
                best.example = first_ex
                best.weight = w
                best.method = "weight_tfidf"

    return best
