from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async
from typing import List
from tg_bot.modules.helper_funcs.filters import CustomFilters

import telegram
from tg_bot import dispatcher

@run_async
def leave(bot: Bot, update: Update, args: List[str]):
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        update.effective_message.reply_text("Please give me a valid chat_id!")
    
    try:
        bot.leaveChat(int(chat_id))
        update.effective_message.reply_text("Left the group successfully!")
    except telegram.TelegramError:
        update.effective_message.reply_text("Attempt failed.")

__help__ = "Leaves a chat. Uses only one paramater: chat_id"

__mod_name__ = "Leave"

LEAVE_HANDLER = CommandHandler("leave", leave, pass_args = True, filters=CustomFilters.sudo_filter)
dispatcher.add_handler(LEAVE_HANDLER)