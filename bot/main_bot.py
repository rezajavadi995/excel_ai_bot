from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN
from bot.handlers import start, handle_message, handle_callback

updater = Updater(BOT_TOKEN)

dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(filters.text & ~filters.command, handle_message))
dp.add_handler(CallbackQueryHandler(handle_callback))

print("✅ ربات در حال اجراست")
updater.start_polling()
updater.idle()
