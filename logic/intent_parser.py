import json

class IntentParser:
    def __init__(self, ai_client):
        self.ai = ai_client

    def build_prompt(self, user_text, excel_context):
        """
        excel_context شامل:
        - sheet names
        - columns
        - column types
        """
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
        prompt = self.build_prompt(user_text, excel_context)

        response = self.ai.complete(prompt)

        try:
            blueprint = json.loads(response)
            return blueprint
        except json.JSONDecodeError:
            raise ValueError("AI output is not valid JSON")
