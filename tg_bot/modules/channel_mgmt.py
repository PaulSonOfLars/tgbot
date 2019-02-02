from io import BytesIO
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.users_sql as sql


from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters


@run_async
def chats(bot: Bot, update: Update):
    message = update.effective_message
    chats = sql.get_all_chats() or []

    chatlist = ''
    for chat in chats:
        chatlist += "●{} ({})\n".format(chat.chat_name, chat.chat_id)


    text = "List of Groups the bot is member of:\n\n"+chatlist

    if message.reply_to_message:
        message.reply_to_message.reply_text(text)
    else:
        message.reply_text(text, quote=False)




@run_async
def add_channel(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    data = args[1]
    args2 = data.split(None, 1)
    channel_id = args2[0]
    channel_name = args2[1]
    retval = sql.add_channel(channel_id, channel_name)

    if retval:
        text = "Channel "+channel_name+" ("+channel_id+") has been added to the List"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)
    else:
        text = "Channel "+channel_name+" ("+channel_id+") is already on your List"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)





@run_async
def del_channel(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    channel_id = args[1]
    retval = sql.del_channel(channel_id)
    if retval:
        text = "Channel "+args[1]+" has been removed from the List"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)
    else:
        text = "Channel "+args[1]+" is not on your List"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)




@run_async
def list_channels(bot: Bot, update: Update):
    message = update.effective_message
    chats = sql.get_all_channels() or []

    chatlist = ''
    for chat in chats:
        chatlist += "●{} ({})\n".format(chat.chat_name, chat.chat_id)


    if len(chats) >= 1:
        text = "List of Channels the bot has been manually added to:\n\n"+chatlist
    else:
        text = "There are no Channels added to your List"

    if message.reply_to_message:
        message.reply_to_message.reply_text(text)
    else:
        message.reply_text(text, quote=False)




__help__ = """This module allows you to expand the gban feature to channels your bot is a member of.
In Order to gban a user from your channels also you need to add the channel to the list.

*Admin only:*
 - /list_channels : Will show you a list of all manually added channels
 - /list_chats : Will show you a list of chats your bot is member of

 - /add_channel <chat id> <channel name> : Adds a channel to your List
 - /del_channel <chat id> : Removes a channel from your List


"""  # no help string

__mod_name__ = "Channel Management"


CHATSS_HANDLER = CommandHandler("list_chats", chats, filters=CustomFilters.sudo_filter)


ADDCHANNEL_HANDLER = CommandHandler("add_channel", add_channel, filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
LISTCHANNELS_HANDLER = CommandHandler("list_channels", list_channels, filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
DELCHANNEL_HANDLER = CommandHandler("del_channel", del_channel, filters=CustomFilters.sudo_filter | CustomFilters.support_filter)



dispatcher.add_handler(CHATSS_HANDLER)

dispatcher.add_handler(ADDCHANNEL_HANDLER)
dispatcher.add_handler(DELCHANNEL_HANDLER)
dispatcher.add_handler(LISTCHANNELS_HANDLER)