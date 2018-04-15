import re

from telegram import Message, Update, Bot, User
from telegram import MessageEntity
from telegram.ext import Filters, run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler

@run_async
def tidy(bot: Bot, update: Update):
    message = update.effective_message
    reply_text = re.sub(r'Pls', "Please", message.reply_to_message.text)
    reply_text = re.sub(r'Plz', "Please", reply_text)
    reply_text = re.sub(r'(sar|sur|Sar|Sur)', "sir", reply_text)
    message.reply_to_message.reply_text(reply_text)

TIDY_HANDLER = DisableAbleCommandHandler("tidy", tidy)

dispatcher.add_handler(TIDY_HANDLER)