from tg_bot import dispatcher, LOGGER
from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters


def spam_filter(bot: Bot, update: Update):
    msg = update.effective_message.text
    LOGGER.debug("spam" in msg)
    if msg and "spam" in msg:
        user = update.effective_user.username
        update.effective_message.reply_text(f"Non spammare! @{user}", quote=False)
        update.effective_message.delete()


SPAM_HANDLER = MessageHandler(Filters.all & Filters.group, spam_filter)

dispatcher.add_handler(SPAM_HANDLER)
