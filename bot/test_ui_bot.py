from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext
)

from config import BOT_TOKEN, ADMIN_ID

# =============================
# ابزار کمکی
# =============================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# =============================
# START
# =============================
def start(update: Update, context: CallbackContext):
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("📊 کار با اکسل", callback_data="excel_menu")],
        [InlineKeyboardButton("🧠 دستورات هوشمند", callback_data="ai_menu")],
        [InlineKeyboardButton("📘 آموزش کامل", callback_data="help_menu")],
    ]

    if is_admin(user.id):
        keyboard.append(
            [InlineKeyboardButton("🛠 مدیریت ربات", callback_data="admin_menu")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "به Excel AI Bot خوش آمدی 👋\n"
        "از دکمه‌ها استفاده کن. هر بخش آموزش جدا دارد.",
        reply_markup=reply_markup
    )

# =============================
# CALLBACK HANDLER
# =============================
def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    query.answer()

    # ---- Excel Menu ----
    if data == "excel_menu":
        keyboard = [
            [InlineKeyboardButton("➕ افزودن گروهی", callback_data="excel_add")],
            [InlineKeyboardButton("✏️ ویرایش ستونی", callback_data="excel_edit")],
            [InlineKeyboardButton("🧪 پیش‌نمایش تغییرات", callback_data="excel_preview")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_home")],
        ]
        query.edit_message_text(
            "📊 بخش کار با اکسل\n"
            "هر عملیات قبل از اجرا قابل پیش‌نمایش و بازگشت است.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ---- AI Menu ----
    elif data == "ai_menu":
        keyboard = [
            [InlineKeyboardButton("✍️ ارسال دستور متنی", callback_data="ai_text")],
            [InlineKeyboardButton("📌 مثال‌ها", callback_data="ai_examples")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_home")],
        ]
        query.edit_message_text(
            "🧠 دستورات هوشمند\n"
            "می‌تونی با زبان فارسی دستور بدی.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ---- Help Menu ----
    elif data == "help_menu":
        query.edit_message_text(
            "📘 آموزش کامل\n\n"
            "مثال:\n"
            "«ستون price رو ۱۰ درصد افزایش بده»\n"
            "«ردیف‌های خالی رو حذف کن»\n\n"
            "همه تغییرات برگشت‌پذیر هستند.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_home")]]
            )
        )

    # ---- Admin Menu ----
    elif data == "admin_menu":
        if not is_admin(user_id):
            query.edit_message_text("⛔ دسترسی غیرمجاز")
            return

        keyboard = [
            [InlineKeyboardButton("⚙️ تنظیمات ربات", callback_data="admin_settings")],
            [InlineKeyboardButton("📂 مدیریت فایل‌ها", callback_data="admin_files")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_home")],
        ]
        query.edit_message_text(
            "🛠 پنل مدیریت\n"
            "این بخش فقط برای مدیر قابل مشاهده است.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ---- Back Home ----
    elif data == "back_home":
        start(update, context)

# =============================
# MESSAGE HANDLER (AI TEXT)
# =============================
def handle_text(update: Update, context: CallbackContext):
    text = update.message.text

    update.message.reply_text(
        "📥 دستور دریافت شد:\n"
        f"`{text}`\n\n"
        "در نسخه نهایی، این دستور به Blueprint تبدیل می‌شود.",
        parse_mode="Markdown"
    )

# =============================
# MAIN
# =============================
def main():
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Test UI Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
