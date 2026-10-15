import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import BOT_TOKEN, CHANNEL_ID, LOCAL_API_URL
from app.handlers import handle_delete, handle_quality, handle_url, help_cmd, id_cmd, start

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    if not BOT_TOKEN or BOT_TOKEN in ("ISI_TOKEN_BOT_KAMU_DI_SINI", "PUT_YOUR_BOT_TOKEN_HERE"):
        print("⚠️  Isi BOT_TOKEN dulu di config.json!")
        return

    builder = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .connect_timeout(30)
        .read_timeout(600)
        .write_timeout(600)
        .pool_timeout(30)
    )
    if LOCAL_API_URL:
        builder = (
            builder.base_url(f"{LOCAL_API_URL}/bot")
            .base_file_url(f"{LOCAL_API_URL}/file/bot")
            .local_mode(True)
        )
        log.info("Mode API: Local Bot API (%s)", LOCAL_API_URL)
    else:
        log.info("Mode API: server resmi Telegram (limit 50MB)")
    log.info("Tujuan video: %s", CHANNEL_ID or "chat user")

    app = builder.build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(handle_quality, pattern=r"^q\|"))
    app.add_handler(CallbackQueryHandler(handle_delete, pattern=r"^del\|"))
    logging.getLogger("httpx").setLevel(logging.WARNING)  # jangan cetak token di log
    log.info("Bot jalan... tekan Ctrl+C untuk berhenti.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

