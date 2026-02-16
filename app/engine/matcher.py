from app.engine.normalize import normalize
from app.engine.weights import WEIGHTS

def _simple_signature(text: str) -> dict:
    # MVP signature (not final prosody):
    # length + split by ".." or "." as caesura hint
    t = normalize(text)
    parts = [p.strip() for p in t.replace("..", ".").split(".") if p.strip()]
    return {
        "text": t,
        "chars": len(t.replace(" ", "")),
        "words": len(t.split()) if t else 0,
        "parts": len(parts),
        "part_words": [len(p.split()) for p in parts] if parts else [],
    }

def analyze_text(text: str) -> dict:
    if not text or not text.strip():
        return {"ok": False, "reason": "empty"}

    sig = _simple_signature(text)

    # MVP rule: لا نرجّح وزن إلا لو عندنا تطابق قوي حسب قواعد ستتوسع
    # الآن: فقط “قواعد أولية” تحفظنا من الغلط
    candidates = []

    # قاعدة مبدئية للمجرشة: غالبًا بيت مقسوم لشطرين + عدد كلمات متوسط
    if sig["parts"] in (1, 2) and 6 <= sig["words"] <= 16:
        candidates.append(("majrasha", 0.55))

    # تجليبة/طويل: تميل لطول أعلى
    if sig["chars"] >= 24 and sig["words"] >= 6:
        candidates.append(("tajleeba", 0.50))
        candidates.append(("tawil", 0.45))

    # موشح/هجري: لو فيه تقسيم واضح/إيقاع أقصر
    if sig["parts"] == 2 and sig["part_words"] and all(w <= 8 for w in sig["part_words"]):
        candidates.append(("muwashah", 0.45))
        candidates.append(("hijri", 0.40))

    # أبوذية: غالبًا أقصر + قفل صوتي (MVP: كلمات أقل)
    if sig["words"] <= 10:
        candidates.append(("abuthiya", 0.35))

    # لو مفيش مرشح قوي -> غير مطابق (أهم نقطة للدقة)
    if not candidates:
        return {
            "ok": True,
            "matched": False,
            "message": "غير مطابق للأوزان المدعومة حالياً",
            "supported": [w["name"] for w in WEIGHTS],
        }

    # اختار الأعلى
    best_key, best_conf = sorted(candidates, key=lambda x: x[1], reverse=True)[0]
    w = next(x for x in WEIGHTS if x["key"] == best_key)

    # لو الثقة أقل من 0.6 -> لا نعطي حكم نهائي
    if best_conf < 0.60:
        return {
            "ok": True,
            "matched": False,
            "message": "تعذّر تحديد الوزن بثقة كافية ضمن القواعد الحالية",
            "candidates": [
                {"name": next(x["name"] for x in WEIGHTS if x["key"] == k), "confidence": c}
                for k, c in sorted(candidates, key=lambda x: x[1], reverse=True)[:3]
            ],
        }

    return {
        "ok": True,
        "matched": True,
        "weight": w["name"],
        "taf3eelat": w["taf3eelat"],
        "confidence": best_conf,
    }
