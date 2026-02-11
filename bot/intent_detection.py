from __future__ import annotations

from dataclasses import dataclass

try:
    import regex as _rx
except Exception:  # pragma: no cover
    import re as _rx

try:
    import spacy
except Exception:  # pragma: no cover
    spacy = None


@dataclass
class Intent:
    name: str
    target: str | None = None
    mode: str | None = None
    confidence: float = 0.0
    raw_text: str = ""


class IntentDetectionEngine:
    def __init__(self):
        self._patterns = {
            "analyze": _rx.compile(r"(آنالیز|تحلیل|analy[sz]e)", _rx.IGNORECASE),
            "filter": _rx.compile(r"(فیلتر|filter)", _rx.IGNORECASE),
            "export": _rx.compile(r"(خروجی|اکسپورت|export|دریافت فایل)", _rx.IGNORECASE),
            "back": _rx.compile(r"(بازگشت|back)", _rx.IGNORECASE),
            "reset": _rx.compile(r"(ریست|لغو|reset|exit)", _rx.IGNORECASE),
            "help": _rx.compile(r"(راهنما|help)", _rx.IGNORECASE),
            "add": _rx.compile(r"(افزودن|اضافه)", _rx.IGNORECASE),
            "delete": _rx.compile(r"(حذف|پاک)", _rx.IGNORECASE),
            "edit": _rx.compile(r"(ویرایش|ادیت|تغییر)", _rx.IGNORECASE),
        }
        if spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                self.nlp = spacy.blank("en")
        else:
            self.nlp = None

    def detect(self, text: str) -> Intent:
        text = (text or "").strip()
        if not text:
            return Intent(name="unknown", confidence=0.0, raw_text=text)

        for name, pat in self._patterns.items():
            if pat.search(text):
                target = self._target_detection(text)
                mode = "group" if _rx.search(r"(گروهی|چند|لیست)", text, _rx.IGNORECASE) else "single"
                return Intent(name=name, target=target, mode=mode, confidence=0.8, raw_text=text)

        target = self._target_detection(text)
        if target:
            return Intent(name="operation", target=target, confidence=0.4, raw_text=text)
        return Intent(name="unknown", confidence=0.1, raw_text=text)

    def _target_detection(self, text: str) -> str | None:
        if _rx.search(r"(ستون|column)", text, _rx.IGNORECASE):
            return "column"
        if _rx.search(r"(سطر|row)", text, _rx.IGNORECASE):
            return "row"
        if _rx.search(r"(فایل|file)", text, _rx.IGNORECASE):
            return "file"

        if self.nlp:
            doc = self.nlp(text)
            for token in doc:
                val = token.text.lower()
                if val in {"column", "row", "file", "filter", "export"}:
                    return val
        return None
