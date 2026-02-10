from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import admin_options, edit_options, main_menu
from config import ADMIN_ID
from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from core.excel_reader import ExcelReader
from logic.blueprint_validator import BlueprintValidator
from logic.fake_ai import FakeAI
from logic.intent_parser import IntentParser

ai = FakeAI()
parser = IntentParser(ai)
user_sessions: dict[int, dict] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "سلام! 👋\nبا /start می‌تونی از من برای تحلیل و ویرایش اکسل استفاده کنی.",
        reply_markup=main_menu(chat_id == ADMIN_ID),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    is_admin = chat_id == ADMIN_ID

    if text == "📊 آنالیز اکسل":
        reader = ExcelReader("storage/uploads/test.xlsx")
        wb = reader.load()
        sheet = reader.get_sheet(wb.sheetnames[0])
        analyzer = ExcelAnalyzer(sheet)
        columns = analyzer.analyze_columns()
        user_sessions[chat_id] = {"reader": reader, "sheet": sheet, "columns": columns}
        await update.message.reply_text(
            "ستون‌ها آماده شد. می‌تونی با دکمه‌ها تغییر بدی یا یک دستور متنی AI بفرستی.\n"
            "مثال: ستون price رو 10 درصد افزایش بده",
            reply_markup=edit_options(columns),
        )
        return

    if text == "⚙️ مدیریت" and is_admin:
        await update.message.reply_text("تنظیمات مدیریتی:", reply_markup=admin_options())
        return

    if text == "📚 راهنما":
        await update.message.reply_text(
            "مثال کاربران:\n"
            "- ستون price رو ۱۰ درصد افزایش بده\n"
            "- ستون price رو حذف کن\n\n"
            "مثال مدیر:\n"
            "- ورود به ⚙️ مدیریت و دیدن وضعیت ربات",
        )
        return

    # مسیر AI text
    session = user_sessions.get(chat_id)
    if session:
        try:
            blueprint = parser.parse(text, {"sheets": [session["sheet"].title], "columns": session["columns"]})
            BlueprintValidator(session["columns"]).validate(blueprint)
            ExcelEditor(session["sheet"]).execute_blueprint(blueprint, session["columns"])
            session["reader"].save()
            await update.message.reply_text(f"✅ انجام شد:\n{blueprint}")
        except Exception as exc:  # noqa: BLE001 - پیام کاربرپسند
            await update.message.reply_text(f"❌ خطا در پردازش دستور: {exc}")
    else:
        await update.message.reply_text("ابتدا گزینه 📊 آنالیز اکسل را انتخاب کنید.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    data = query.data
    session = user_sessions.get(chat_id)

    if data.startswith("admin:"):
        if chat_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        await query.answer(f"✅ عملیات مدیریتی: {data.split(':', 1)[1]}", show_alert=True)
        return

    if not session:
        await query.answer("ابتدا 📊 آنالیز اکسل را بزنید", show_alert=True)
        return

    columns = session["columns"]
    editor = ExcelEditor(session["sheet"])

    if data.startswith("inc:"):
        col = data.split(":", 1)[1]
        editor.increase_percentage(columns[col]["index"], 10)
        message = f"{col} ↑ ۱۰٪"
    elif data.startswith("dec:"):
        col = data.split(":", 1)[1]
        editor.increase_percentage(columns[col]["index"], -10)
        message = f"{col} ↓ ۱۰٪"
    elif data.startswith("del:"):
        col = data.split(":", 1)[1]
        editor.delete_column(columns[col]["index"])
        message = f"{col} حذف شد"
    else:
        await query.answer("گزینه نامعتبر")
        return

    session["reader"].save()
    await query.answer(message, show_alert=True)
