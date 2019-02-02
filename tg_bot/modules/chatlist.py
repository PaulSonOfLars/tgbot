from io import BytesIO
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.users_sql as sql


import tg_bot.modules.sql.channel_mgmt_sql as sql2

from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters


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


def list_channels(bot: Bot, update: Update):
    chats = sql.get_all_chats() or []

    chatfile = 'List of chats.\n'
    for chat in chats:
        chatfile += "[x] {} - {}\n".format(chat.chat_name, chat.chat_id)

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(document=output, filename="chatlist.txt",
                                                caption="Here is the list of chats in my database.")




@run_async
def add_channel(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    text = "Channel "+args[1]+" has been added to the List"
    if message.reply_to_message:
        message.reply_to_message.reply_text(text)
    else:
        message.reply_text(text, quote=False)




@run_async
def del_channel(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    text = "Channel "+args[1]+" has been removed from the List"
    if message.reply_to_message:
        message.reply_to_message.reply_text(text)
    else:
        message.reply_text(text, quote=False)



@run_async
def list_channels(bot: Bot, update: Update):
    text = "Here is your List of manually added Channels:\n-fake1\n-fake2"
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(text)
    else:
        message.reply_text(text, quote=False)




__help__ = ""  # no help string

__mod_name__ = "chatlist"


CHATSS_HANDLER = CommandHandler("chats", chats, filters=CustomFilters.sudo_filter)


ADDCHANNEL_HANDLER = CommandHandler("add_channel", add_channel, filters=CustomFilters.sudo_filter)
LISTCHANNELS_HANDLER = CommandHandler("list_channels", list_channels, filters=CustomFilters.sudo_filter)
DELCHANNEL_HANDLER = CommandHandler("del_channel", del_channel, filters=CustomFilters.sudo_filter)




dispatcher.add_handler(CHATSS_HANDLER)

dispatcher.add_handler(ADDCHANNEL_HANDLER)
dispatcher.add_handler(DELCHANNEL_HANDLER)
dispatcher.add_handler(LISTCHANNELS_HANDLER)