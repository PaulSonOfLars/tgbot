from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import bot_can_delete

FORBIDDEN_ENTITY_TYPES = ["url", "text_link", "email", "phone_number"]


@run_async
@bot_can_delete
def spam_filter(bot: Bot, update: Update):
    """
    Filter messages with spam into message's text
    """
    msg = update.effective_message.text
    message_entities = update.effective_message.parse_entities()
    message_caption_entities = update.effective_message.parse_caption_entities()

    found = False
    for descriptor, entity in message_entities.items():
        LOGGER.debug(f"Found message entity: {descriptor['type']} {entity}")
        if descriptor["type"] in FORBIDDEN_ENTITY_TYPES:
            found = True

    if found:
        spam_action(update)


def spam_action(update: Update):
    user = update.effective_user.username
    update.effective_message.reply_text(f"Non spammare! @{user}", quote=False)
    update.effective_message.delete()


def white_spam_add(bot: Bot, update: Update):
    if update.effective_message.reply_to_message:
        pass
    else:
        update.effective_message.reply_text("Cosa vuoi aggiungere in whitelist?")


SPAM_HANDLER = MessageHandler(Filters.all & Filters.group, spam_filter)
WHITE_SPAM_HANDLER = CommandHandler("whitespam", white_spam_add)
dispatcher.add_handler(SPAM_HANDLER)
