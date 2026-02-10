import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from bot.handlers import start, handle_message, handle_callback

async def main():
    # ساخت ربات
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ثبت handler ها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ ربات در حال اجراست")
    await app.start_polling()
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
