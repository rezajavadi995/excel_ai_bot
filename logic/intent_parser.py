from __future__ import annotations

import json
import re


class IntentParser:
    def __init__(self, ai_client):
        self.ai = ai_client

    def build_prompt(self, user_text, excel_context):
        return f"""
تو یک مترجم حرفه‌ای دستور اکسل هستی.
وظیفه تو فقط تبدیل دستور کاربر به JSON است.
هیچ توضیحی ننویس.
هیچ متنی خارج از JSON ننویس.

قوانین:
- فقط از ستون‌های داده‌شده استفاده کن
- اگر دستور نامشخص است، error برگردان
- اگر عملیات غیرممکن است، error برگردان

ساختار خروجی دقیقاً این است:
{{
  "sheet": "",
  "action": "",
  "target": {{}},
  "condition": null,
  "operation": {{}}
}}

اطلاعات فایل اکسل:
{json.dumps(excel_context, ensure_ascii=False)}

دستور کاربر:
"{user_text}"
"""

    def parse(self, user_text, excel_context):
        response = self.ai.complete(self.build_prompt(user_text, excel_context)).strip()

        # بعضی مدل‌ها JSON را داخل ```json``` برمی‌گردانند
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", response, re.DOTALL)
        if fenced:
            response = fenced.group(1)

        blueprint = json.loads(response)
        if "error" in blueprint:
            raise ValueError(f"AI error: {blueprint['error']}")
        return blueprint
