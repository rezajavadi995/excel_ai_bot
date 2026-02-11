from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParsedIntent:
    op_kind: str
    target_kind: str
    mode: str


class IntentAnalyzer:
    """Rule + lightweight NLP (keyword matching)."""

    def parse(self, text: str) -> ParsedIntent | None:
        normalized = text.strip().replace("ي", "ی").replace("ك", "ک")

        op_kind = None
        if any(k in normalized for k in ["حذف", "پاک"]):
            op_kind = "delete"
        elif any(k in normalized for k in ["ادیت", "ویرایش", "تغییر"]):
            op_kind = "edit"
        elif any(k in normalized for k in ["افزود", "اضافه"]):
            op_kind = "add"

        if not op_kind:
            return None

        target_kind = "column" if any(k in normalized for k in ["ستون", "column"]) else "row"
        mode = "group" if any(k in normalized for k in ["گروهی", "چند", "لیست"]) else "single"

        return ParsedIntent(op_kind=op_kind, target_kind=target_kind, mode=mode)
