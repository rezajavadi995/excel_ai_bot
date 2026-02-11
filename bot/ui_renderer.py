from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.context_manager import FSMState, UserContext


class UIRenderer:
    def reply_menu(self, ctx: UserContext) -> ReplyKeyboardMarkup:
        rows = [[KeyboardButton("📊 آنالیز"), KeyboardButton("🧪 فیلتر")], [KeyboardButton("📤 خروجی"), KeyboardButton("📚 راهنما")]]
        rows.append([KeyboardButton("⬅️ بازگشت"), KeyboardButton("🧹 ریست")])
        if ctx.state == FSMState.WAIT_FILE:
            rows.insert(0, [KeyboardButton("📤 ارسال فایل")])
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)

    def inline_menu(self, ctx: UserContext, suggest_export: bool = False) -> InlineKeyboardMarkup:
        rows = [
            [InlineKeyboardButton("📊 Analyze file", callback_data="intent:analyze")],
            [InlineKeyboardButton("🧪 Filter data", callback_data="intent:filter")],
            [InlineKeyboardButton("📤 Export result", callback_data="intent:export")],
            [InlineKeyboardButton("📁 Use previous analysis", callback_data="intent:reuse")],
        ]
        if suggest_export:
            rows.insert(0, [InlineKeyboardButton("💡 پیشنهاد: Export", callback_data="intent:export")])
        rows.extend(
            [
                [InlineKeyboardButton("⬅️ Back", callback_data="intent:back")],
                [InlineKeyboardButton("🧹 Reset", callback_data="intent:reset")],
            ]
        )
        return InlineKeyboardMarkup(rows)

    def analysis_text(self, analysis: dict) -> str:
        lines = ["✅ تحلیل فایل کامل شد", ""]
        for i, sh in enumerate(analysis.get("sheets", []), start=1):
            lines.append(f"Sheet {i}: {sh['name']}")
            lines.append(f"- Rows: {sh['rows']}")
            lines.append(f"- Columns: {sh['cols']}")
            lines.append("- Headers:")
            for h in sh.get("headers", []):
                lines.append(f"  • {h}")
            lines.append("")
        lines.append("حالا عملیات بعدی را انتخاب کنید.")
        return "\n".join(lines)

    @staticmethod
    def help_text() -> str:
        return (
            "راهنما:\n"
            "1) فایل اکسل را ارسال کن\n"
            "2) Analyze file\n"
            "3) Filter data\n"
            "4) Export result"
        )
