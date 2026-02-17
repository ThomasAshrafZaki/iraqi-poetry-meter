"""
تطبيع النص الشعبي العراقي.
ملاحظة: التطبيع العميق (deep) قد يغير المعنى، استخدمه فقط في exact match.
"""

from __future__ import annotations

import re
from typing import List, Set, Optional

# إزالة الحركات والتشكيل
_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")  # ً ٌ ٍ َ ُ ِ ّ ْ ٰ

# استبدال الحروف المتشابهة (آمن)
_LETTER_MAP = {
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا',      # توحيد الألف
    'ة': 'ه',                           # تاء مربوطة
    'ى': 'ي',                            # ألف مقصورة
    'ؤ': 'و', 'ئ': 'ي',                  # همزة على واو وياء
    'ء': '',                              # حذف الهمزة المنفردة
    'گ': 'ك', 'ڭ': 'ك', 'ڨ': 'ق',        # أشكال الكاف والقاف العامية
    'چ': 'ج',                             # الجيم المعطشة
    'پ': 'ب',                             # الباء الأعجمية
}

# قائمة اختيارية للكلمات العامية (استخدم بحذر شديد)
_COMMON_REPLACEMENTS = {
    'هذا': 'هاي',
    'هذه': 'هاي',
    'ذلك': 'ذاك',
    'الذي': 'الي',
    'التي': 'الي',
    'الذين': 'الين',
    'كيف': 'شلون',
    'ماذا': 'شو',
    'لماذا': 'ليش',
}

_PUNCT = re.compile(r"[^\w\s\u0600-\u06FF]", re.UNICODE)
_MULTI_SPACE = re.compile(r"\s+")
_TATWEEL = re.compile(r"ـ+")

def normalize_arabic(text: str, deep: bool = False) -> str:
    """
    تطبيع النص العربي/العراقي.
    deep=True يطبق تحويلات لهجوية (قد تغير المعنى، استخدم بحذر).
    """
    if not isinstance(text, str):
        return ""
    t = text.strip()
    if not t:
        return ""

    t = _TATWEEL.sub("", t)
    t = _DIACRITICS.sub("", t)

    for old, new in _LETTER_MAP.items():
        t = t.replace(old, new)

    if deep:
        # تطبيق تحويلات لهجوية على الكلمات الكاملة فقط
        words = t.split()
        normalized_words = []
        for w in words:
            if len(w) <= 2:
                normalized_words.append(w)
                continue
            found = False
            for key, val in _COMMON_REPLACEMENTS.items():
                if w == key or w == val:
                    normalized_words.append(val)
                    found = True
                    break
            if not found:
                normalized_words.append(w)
        t = ' '.join(normalized_words)

    t = _PUNCT.sub(" ", t)
    t = _MULTI_SPACE.sub(" ", t)
    return t.strip()

def tokenize(text: str) -> List[str]:
    """تقطيع النص إلى كلمات بعد التطبيع."""
    return normalize_arabic(text, deep=False).split()

def char_ngrams(text: str, n: int = 2) -> Set[str]:
    """n-grams حرفية."""
    t = normalize_arabic(text, deep=False).replace(' ', '')
    if len(t) < n:
        return {t} if t else set()
    return {t[i:i+n] for i in range(len(t)-n+1)}

def word_ngrams(text: str, n: int = 2) -> Set[str]:
    """n-grams كلمات."""
    words = tokenize(text)
    if len(words) < n:
        return {' '.join(words)} if words else set()
    return {' '.join(words[i:i+n]) for i in range(len(words)-n+1)}
