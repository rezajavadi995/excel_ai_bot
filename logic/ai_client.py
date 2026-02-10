from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class AIClient:
    def complete(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class RuleBasedAIClient(AIClient):
    """یک موتور ساده محلی برای تبدیل متن فارسی به Blueprint."""

    def complete(self, prompt: str) -> str:
        user_text = self._extract_user_text(prompt).strip()
        columns = self._extract_columns(prompt)

        blueprint = {
            "sheet": "Sheet",
            "action": "update",
            "target": {},
            "condition": None,
            "operation": {},
        }

        col = self._detect_column(user_text, columns)
        if not col:
            return json.dumps({"error": "column_not_found"}, ensure_ascii=False)
        blueprint["target"]["column"] = col

        if "حذف" in user_text:
            blueprint["operation"] = {"type": "delete_column"}
        else:
            percent = self._detect_percent(user_text)
            if percent is None:
                return json.dumps({"error": "operation_not_found"}, ensure_ascii=False)
            if any(token in user_text for token in ["کاهش", "کم", "منفی"]):
                percent *= -1
            blueprint["operation"] = {"type": "percentage_increase", "value": percent}

        return json.dumps(blueprint, ensure_ascii=False)

    @staticmethod
    def _extract_user_text(prompt: str) -> str:
        match = re.search(r'دستور کاربر:\s*"(.*)"', prompt, re.DOTALL)
        return match.group(1) if match else prompt

    @staticmethod
    def _extract_columns(prompt: str) -> list[str]:
        context_match = re.search(r"اطلاعات فایل اکسل:\s*(\{.*\})\s*دستور کاربر:", prompt, re.DOTALL)
        if context_match:
            try:
                context = json.loads(context_match.group(1))
                columns = context.get("columns", {})
                if isinstance(columns, dict):
                    return list(columns.keys())
            except json.JSONDecodeError:
                pass

        # fallback ساده: نام کلیدهای انگلیسی را از متن می‌گیرد
        return re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', prompt)

    @staticmethod
    def _detect_percent(text: str) -> float | None:
        normalized = RuleBasedAIClient._normalize_number_chars(text)
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*درصد", normalized)
        if match:
            return float(match.group(1))
        if any(token in text for token in ["افزایش", "زیاد"]):
            return 10.0
        return None

    @staticmethod
    def _normalize_number_chars(text: str) -> str:
        translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٫", "0123456789.")
        return text.translate(translation)

    @staticmethod
    def _detect_column(text: str, columns: list[str]) -> str | None:
        for col in columns:
            if col in text:
                return col
        return columns[0] if columns else None
