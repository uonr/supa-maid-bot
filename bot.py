#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import re
from dotenv import load_dotenv

load_dotenv()
from picker import pickup


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entities = update.message.entities or update.message.caption_entities or []
    text = update.message.text or update.message.caption or ""
    char_list = list(text)
    has_error = False
    for entity in entities:
        try:
            if entity.type == entity.TEXT_LINK:
                await pickup(entity.url)
            if entity.type == entity.URL:
                url = "".join(char_list[entity.offset : entity.offset + entity.length])
                if url.startswith("https://t.me"):
                    continue
                await pickup(url.strip())
        except RuntimeError as e:
            has_error = True
            logging.warn(e)
            await update.message.reply_text(
                escape_ansi(str(e)),
                disable_web_page_preview=True,
                reply_to_message_id=update.message.id,
            )
    if not has_error:
        await update.message.delete()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat is None:
        return
    await context.bot.send_message(chat_id=chat.id, text="started")


if __name__ == "__main__":
    application = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.ANIMATION)
            & (~filters.COMMAND),
            message_handler,
        )
    )
    application.add_handler(start_handler)

    application.run_polling()
