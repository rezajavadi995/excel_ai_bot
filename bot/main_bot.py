from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    try:
        from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "پکیج python-telegram-bot نصب نیست. ابتدا نصب‌کننده را اجرا کنید یا در venv دستور `pip install -r requirements.txt` بزنید."
        ) from exc

    from bot.handlers import handle_callback, handle_message, start
    from config import BOT_TOKEN

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ ربات در حال اجراست")
    app.run_polling()


if __name__ == "__main__":
    main()
