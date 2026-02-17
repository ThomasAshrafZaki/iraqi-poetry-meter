"""
المحرك الرئيسي لتحليل الوزن.
الآن يقرأ البيانات من JSON مباشرة.
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Tuple, Any, Optional

from app.core.normalize import normalize_arabic
from app.core.similarity import (
    find_best_match, BestMatch, combined_similarity,
    levenshtein_ratio, TfidfVectorizer
)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# تغيير المسار إلى JSON
_DATA_PATH = os.path.join(os.path.dirname(_THIS_DIR), "data", "examples.json")
_EXAMPLES_CACHE: Optional[Dict[str, Any]] = None

def _load_examples() -> Dict:
    """تحميل الأمثلة من ملف JSON."""
    global _EXAMPLES_CACHE
    if _EXAMPLES_CACHE is not None:
        return _EXAMPLES_CACHE

    if not os.path.exists(_DATA_PATH):
        raise FileNotFoundError(f"ملف الأمثلة غير موجود: {_DATA_PATH}. يجب تحويل examples.js إلى examples.json أولاً.")

    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # التأكد من وجود الحقول المطلوبة
    for weight, info in data.items():
        if "taf3eelat" not in info:
            info["taf3eelat"] = ""
        if "examples" not in info or not isinstance(info["examples"], list):
            info["examples"] = []

    _EXAMPLES_CACHE = data
    return data

def list_weights() -> List[str]:
    return sorted(_load_examples().keys())

def _flatten_candidates(data: Dict) -> List[Tuple[str, str]]:
    candidates = []
    for weight, info in data.items():
        for ex in info.get("examples", []):
            if isinstance(ex, str) and ex.strip():
                candidates.append((weight, ex.strip()))
    return candidates

def _build_weight_profiles(data: Dict) -> Dict[str, str]:
    """بناء نص مركب لكل وزن (يجمع كل أمثلته) لمقارنة TF-IDF."""
    profiles = {}
    for weight, info in data.items():
        examples = [ex.strip() for ex in info.get("examples", []) if isinstance(ex, str) and ex.strip()]
        if examples:
            profiles[weight] = ' '.join(examples)
    return profiles

def _exact_match(text: str, candidates: List[Tuple[str, str]]) -> Tuple[bool, str, str]:
    """
    تطابق تام على مرحلتين:
    1. deep=False (تطبيع خفيف)
    2. deep=True (تطبيع عميق) كـ fallback
    """
    # المرحلة الأولى: deep=False
    norm_input_light = normalize_arabic(text, deep=False)
    compact_light = re.sub(r'\s+', '', norm_input_light)

    for w, ex in candidates:
        norm_ex_light = normalize_arabic(ex, deep=False)
        compact_light_ex = re.sub(r'\s+', '', norm_ex_light)
        if compact_light == compact_light_ex:
            return True, w, ex
        # تشابه عالٍ جداً
        if abs(len(compact_light) - len(compact_light_ex)) <= 2:
            sim = levenshtein_ratio(compact_light, compact_light_ex)
            if sim > 0.95:
                return True, w, ex

    # المرحلة الثانية: deep=True (تجربة التطبيع العميق)
    norm_input_deep = normalize_arabic(text, deep=True)
    compact_deep = re.sub(r'\s+', '', norm_input_deep)

    for w, ex in candidates:
        norm_ex_deep = normalize_arabic(ex, deep=True)
        compact_deep_ex = re.sub(r'\s+', '', norm_ex_deep)
        if compact_deep == compact_deep_ex:
            return True, w, ex
        if abs(len(compact_deep) - len(compact_deep_ex)) <= 2:
            sim = levenshtein_ratio(compact_deep, compact_deep_ex)
            if sim > 0.95:
                return True, w, ex

    return False, "", ""

def analyze_poem_line(text: str) -> Dict:
    data = _load_examples()
    candidates = _flatten_candidates(data)
    weight_profiles = _build_weight_profiles(data)

    if not candidates:
        return {
            "ok": False,
            "error": "no_examples",
            "message": "لا توجد أمثلة في قاعدة البيانات."
        }

    # 1. تطابق تام
    exact, w, ex = _exact_match(text, candidates)
    if exact:
        info = data.get(w, {})
        return {
            "ok": True,
            "matched": True,
            "input": text,
            "normalized": normalize_arabic(text, deep=False),
            "weight": w,
            "taf3eelat": info.get("taf3eelat", ""),
            "confidence": 1.0,
            "closest_example": ex,
            "method": "exact_match"
        }

    # 2. تجهيز TfidfVectorizer على كل الأمثلة
    all_examples = [ex for _, ex in candidates]
    vectorizer = TfidfVectorizer(all_examples) if all_examples else None

    # 3. بحث أفضل تطابق
    best = find_best_match(text, candidates, weight_profiles, vectorizer)

    # 4. عتبة ثقة ديناميكية
    confidence = best.score
    if confidence < 0.3:
        return {
            "ok": True,
            "matched": False,
            "input": text,
            "normalized": normalize_arabic(text, deep=False),
            "confidence": round(confidence, 3),
            "message": "البيت بعيد عن جميع الأوزان المدعومة حالياً. يرجى إضافة أمثلة أقرب."
        }

    info = data.get(best.weight, {})
    return {
        "ok": True,
        "matched": True,
        "input": text,
        "normalized": normalize_arabic(text, deep=False),
        "weight": best.weight,
        "taf3eelat": info.get("taf3eelat", ""),
        "confidence": round(confidence, 3),
        "closest_example": best.example,
        "method": best.method
    }
