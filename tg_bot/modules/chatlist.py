from io import BytesIO
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.users_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters

USERS_GROUP=4

@run_async
def chats(bot: Bot, update: Update):
    chats = sql.get_all_chats() or []

    chatfile = 'List of chats.\n'
    for chat in chats:
        chatfile += "[x] {} - {}\n".format(chat.chat_name, chat.chat_id)

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(document=output, filename="chatlist.txt",
                                                caption="Here is the list of chats in my database.")

__help__ = ""  # no help string

__mod_name__ = "chatlist"


CHATSS_HANDLER = CommandHandler("chats", chats, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(CHATSS_HANDLER)
