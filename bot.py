from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from config import BOT_TOKEN
from handlers import (
    start, handle_message,
    kishi_callback, direction_callback,
    time_callback, add_extra_callback,
    finish_order_callback, new_order_callback
)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start va matnli xabarlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback tugmalar
    app.add_handler(CallbackQueryHandler(kishi_callback, pattern="^kishi_"))
    app.add_handler(CallbackQueryHandler(direction_callback, pattern="^yo_"))
    app.add_handler(CallbackQueryHandler(time_callback, pattern="^vaqt_"))
    app.add_handler(CallbackQueryHandler(add_extra_callback, pattern="^add_extra$"))
    app.add_handler(CallbackQueryHandler(finish_order_callback, pattern="^finish_order$"))

    app.add_handler(CallbackQueryHandler(new_order_callback, pattern="^new_order$"))

    app.run_polling()

if __name__ == "__main__":
    main()
