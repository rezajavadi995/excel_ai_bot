from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters


def main():
    from bot.handlers import handle_callback, handle_message, start
    from config import BOT_TOKEN

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Test UI Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
