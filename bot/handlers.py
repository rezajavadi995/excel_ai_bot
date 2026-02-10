from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from bot.keyboards import main_menu, edit_options, admin_options
from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from logic.fake_ai import FakeAI
from logic.intent_parser import IntentParser
from core.excel_reader import ExcelReader
from config import BOT_TOKEN, ADMIN_ID

ai = FakeAI()
parser = IntentParser(ai)

# مدیریت session کاربر (map chat_id -> current sheet, columns)
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_admin = chat_id == ADMIN_ID
    await update.message.reply_text(
        "سلام! خوش آمدید به Excel AI Bot.\nمن می‌توانم اکسل شما را هوشمندانه ویرایش کنم.",
        reply_markup=main_menu(is_admin)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    is_admin = chat_id == ADMIN_ID

    if text == "📊 آنالیز اکسل":
        reader = ExcelReader("storage/uploads/test.xlsx")
        wb = reader.load()
        sheet = reader.get_sheet("Sheet")
        analyzer = ExcelAnalyzer(sheet)
        columns = analyzer.get_column_names()
        user_sessions[chat_id] = {"columns": columns, "sheet": sheet}
        await update.message.reply_text("ستون‌های فایل شما:", reply_markup=edit_options(columns))

    elif text == "⚙️ مدیریت" and is_admin:
        await update.message.reply_text("تنظیمات مدیریتی:", reply_markup=admin_options())
    elif text == "📚 راهنما":
        await update.message.reply_text(
            "آموزش کامل:\n"
            "📊 آنالیز اکسل → مشاهده ستون‌ها و عملیات\n"
            "✏️ ویرایش → انتخاب عملیات روی ستون‌ها\n"
            "⚙️ مدیریت → فقط برای مدیر\n"
        )
    else:
        await update.message.reply_text("دستور نامعتبر یا مسیر فعلی را انتخاب کنید.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # پاسخ اولیه برای حذف لودینگ
    chat_id = query.message.chat.id
    data = query.data

    session = user_sessions.get(chat_id)
    if not session:
        await query.answer("ابتدا گزینه آنالیز اکسل را انتخاب کنید")
        return

    sheet = session["sheet"]
    columns = session["columns"]
    editor = ExcelEditor(sheet)

    if data.startswith("inc:"):
        col = data.split(":")[1]
        editor.increase_percentage(columns[col]["index"], 10)
        await query.answer(f"{col} ↑ ۱۰٪ اعمال شد")
    elif data.startswith("dec:"):
        col = data.split(":")[1]
        editor.increase_percentage(columns[col]["index"], -10)
        await query.answer(f"{col} ↓ ۱۰٪ اعمال شد")
    elif data.startswith("del:"):
        col = data.split(":")[1]
        editor.delete_column(columns[col]["index"])
        await query.answer(f"{col} حذف شد")
    elif data.startswith("admin:"):
        action = data.split(":")[1]
        await query.answer(f"Admin action: {action}")

    # ذخیره تغییرات واقعی
    reader = ExcelReader("storage/uploads/test.xlsx")
    reader.save(sheet)
