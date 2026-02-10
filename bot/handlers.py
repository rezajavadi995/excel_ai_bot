from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import (
    inline_admin_menu,
    inline_ai_menu,
    inline_excel_menu,
    inline_home_menu,
    reply_home_menu,
)
from config import ADMIN_ID
from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from core.excel_reader import ExcelReader
from logic.blueprint_validator import BlueprintValidator
from logic.fake_ai import FakeAI
from logic.intent_parser import IntentParser

UPLOAD_FILE = Path("storage/uploads/test.xlsx")

ai = FakeAI()
parser = IntentParser(ai)
user_sessions: dict[int, dict] = {}


def _ensure_sample_file() -> None:
    UPLOAD_FILE.parent.mkdir(parents=True, exist_ok=True)
    if UPLOAD_FILE.exists():
        return
    wb = Workbook()
    ws = wb.active
    ws.append(["name", "price", "count"])
    ws.append(["item1", 100, 2])
    ws.append(["item2", 200, 4])
    wb.save(UPLOAD_FILE)


def _session(chat_id: int) -> dict:
    return user_sessions.setdefault(chat_id, {"ui_mode": "inline", "menu": "home"})


async def _send_home(update: Update, chat_id: int):
    is_admin = chat_id == ADMIN_ID
    session = _session(chat_id)
    mode = session.get("ui_mode", "inline")
    if mode == "reply":
        await update.effective_message.reply_text(
            "🏠 منوی اصلی (حالت فیزیکی)",
            reply_markup=reply_home_menu(is_admin=is_admin),
        )
    else:
        await update.effective_message.reply_text(
            "🏠 منوی اصلی (حالت شناور)",
            reply_markup=inline_home_menu(is_admin=is_admin),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = _session(chat_id)
    session["menu"] = "home"
    await _send_home(update, chat_id)


async def _analyze_excel(chat_id: int) -> dict:
    _ensure_sample_file()
    reader = ExcelReader(str(UPLOAD_FILE))
    wb = reader.load()
    sheet = reader.get_sheet(wb.sheetnames[0])
    columns = ExcelAnalyzer(sheet).analyze_columns()
    state = _session(chat_id)
    state.update({"reader": reader, "sheet": sheet, "columns": columns, "menu": "excel"})
    return state


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    is_admin = chat_id == ADMIN_ID
    state = _session(chat_id)

    if text in {"/start", "🏠 منوی اصلی"}:
        state["menu"] = "home"
        await _send_home(update, chat_id)
        return

    if text == "🧭 منوی شناور":
        state["ui_mode"] = "inline"
        await update.message.reply_text("✅ حالت شناور فعال شد.")
        await _send_home(update, chat_id)
        return

    if text == "⌨️ منوی فیزیکی":
        state["ui_mode"] = "reply"
        await update.message.reply_text("✅ حالت فیزیکی فعال شد.", reply_markup=reply_home_menu(is_admin=is_admin))
        return

    if text == "📊 آنالیز اکسل":
        state = await _analyze_excel(chat_id)
        await update.message.reply_text(
            "✅ تحلیل انجام شد. عملیات دلخواه را انتخاب کنید.",
            reply_markup=inline_excel_menu(state["columns"]),
        )
        return

    if text == "🤖 دستیار هوشمند":
        state["menu"] = "ai"
        await update.message.reply_text(
            "متن دستور را بفرست. مثال: ستون price رو 10 درصد افزایش بده",
            reply_markup=inline_ai_menu(),
        )
        return

    if text == "⚙️ مدیریت":
        if not is_admin:
            await update.message.reply_text("⛔ فقط مدیر دسترسی دارد")
            return
        await update.message.reply_text("پنل مدیریت:", reply_markup=inline_admin_menu())
        return

    if text == "📚 راهنما":
        await update.message.reply_text(
            "راهنما:\n"
            "1) 📊 آنالیز اکسل\n"
            "2) انتخاب عملیات با دکمه‌های شناور\n"
            "3) یا ارسال دستور فارسی مستقیم\n\n"
            "مثال: ستون price رو ۵ درصد کاهش بده"
        )
        return

    if "sheet" in state and "columns" in state:
        try:
            blueprint = parser.parse(text, {"sheets": [state["sheet"].title], "columns": state["columns"]})
            BlueprintValidator(state["columns"]).validate(blueprint)
            ExcelEditor(state["sheet"]).execute_blueprint(blueprint, state["columns"])
            state["reader"].save()
            await update.message.reply_text(f"✅ انجام شد:\n{blueprint}")
        except Exception as exc:  # noqa: BLE001
            await update.message.reply_text(f"❌ خطا: {exc}")
        return

    await update.message.reply_text("ابتدا /start یا 📊 آنالیز اکسل را انتخاب کن.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    data = query.data
    state = _session(chat_id)

    if data == "nav:home":
        state["menu"] = "home"
        await query.message.reply_text("بازگشت به خانه", reply_markup=inline_home_menu(chat_id == ADMIN_ID))
        return

    if data == "ui:inline":
        state["ui_mode"] = "inline"
        await query.message.reply_text("✅ حالت شناور فعال شد", reply_markup=inline_home_menu(chat_id == ADMIN_ID))
        return

    if data == "ui:reply":
        state["ui_mode"] = "reply"
        await query.message.reply_text("✅ حالت فیزیکی فعال شد", reply_markup=reply_home_menu(chat_id == ADMIN_ID))
        return

    if data == "nav:excel" or data == "excel:analyze":
        state = await _analyze_excel(chat_id)
        await query.message.reply_text("📊 منوی اکسل", reply_markup=inline_excel_menu(state["columns"]))
        return

    if data == "nav:ai":
        state["menu"] = "ai"
        await query.message.reply_text("🤖 منوی AI", reply_markup=inline_ai_menu())
        return

    if data == "ai:examples":
        await query.message.reply_text(
            "نمونه‌ها:\n- ستون price رو 10 درصد افزایش بده\n- ستون count رو حذف کن"
        )
        return

    if data == "ai:text":
        await query.message.reply_text("دستور متنی خود را ارسال کنید.")
        return

    if data == "nav:help":
        await query.message.reply_text("راهنما در منوی اصلی: گزینه 📚 راهنما")
        return

    if data == "nav:admin":
        if chat_id != ADMIN_ID:
            await query.message.reply_text("⛔ دسترسی غیرمجاز")
            return
        await query.message.reply_text("⚙️ پنل مدیریت", reply_markup=inline_admin_menu())
        return

    if data.startswith("admin:"):
        if chat_id != ADMIN_ID:
            await query.message.reply_text("⛔ دسترسی غیرمجاز")
            return
        await query.message.reply_text(f"✅ اجرا شد: {data.split(':', 1)[1]}")
        return

    if data.startswith(("inc:", "dec:", "del:")):
        if "sheet" not in state or "columns" not in state:
            await query.message.reply_text("اول تحلیل اکسل را اجرا کن")
            return

        columns = state["columns"]
        editor = ExcelEditor(state["sheet"])
        col = data.split(":", 1)[1]
        if col not in columns:
            await query.message.reply_text("ستون نامعتبر")
            return

        if data.startswith("inc:"):
            editor.increase_percentage(columns[col]["index"], 10)
            msg = f"{col} ۱۰٪ افزایش"
        elif data.startswith("dec:"):
            editor.increase_percentage(columns[col]["index"], -10)
            msg = f"{col} ۱۰٪ کاهش"
        else:
            editor.delete_column(columns[col]["index"])
            msg = f"{col} حذف شد"

        state["reader"].save()
        await query.message.reply_text(f"✅ {msg}")
        return

    await query.message.reply_text("گزینه نامعتبر")
