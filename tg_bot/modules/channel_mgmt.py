from io import BytesIO
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters, CommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.users_sql as sql

from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters



@run_async
@user_admin
def chats(bot: Bot, update: Update):
    message = update.effective_message
    chats = sql.get_all_chats() or []

    chatlist = ''
    for chat in chats:
        chatlist += "●{} ( <code>{}</code> )\n".format(chat.chat_name, chat.chat_id)


    text = "List of Groups the bot is member of:\n\n"+chatlist

    if message.reply_to_message:
        message.reply_to_message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        message.reply_text(text, quote=False)




@run_async
@user_admin
def add_channel(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    try:
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
    except Exception as e:
        text = "You need to give me a channel id and a name in order to add it!\n/addchannel <chat id> <chat name>"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)




@run_async
@user_admin
def del_channel(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    try:
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
    except Exception as e:
        text = "You need to give me a channel id to delete something!"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)


@run_async
@user_admin
def del_channel(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    channel_id = args[1]

    try:
        retval=bot.leaveChat(channel_id)
    except Exception as e:
        pass

    try:
        retval = sql.del_channel(channel_id)
        if retval:
            text = "Channel "+args[1]+" has been removed from the DB"
            if message.reply_to_message:
                message.reply_to_message.reply_text(text)
            else:
                message.reply_text(text, quote=False)
        else:
            text = "Channel "+args[1]+" is not on your DB"
            if message.reply_to_message:
                message.reply_to_message.reply_text(text)
            else:
                message.reply_text(text, quote=False)
    except Exception as e:
        text = "You need to give me a channel id to delete something!"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)



@run_async
@user_admin
def del_chat(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    channel_id = args[1]

    try:
        retval=bot.leaveChat(channel_id)
    except Exception as e:
        pass

    try:
        retval = sql.del_chat(channel_id)
        if retval:
            text = "Chat "+args[1]+" has been removed from the DB"
            if message.reply_to_message:
                message.reply_to_message.reply_text(text)
            else:
                message.reply_text(text, quote=False)
        else:
            text = "Chat "+args[1]+" is not on your DB"
            if message.reply_to_message:
                message.reply_to_message.reply_text(text)
            else:
                message.reply_text(text, quote=False)
    except Exception as e:
        text = "You need to give me a chat id to delete something!"
        if message.reply_to_message:
            message.reply_to_message.reply_text(text)
        else:
            message.reply_text(text, quote=False)



@run_async
@user_admin
def list_channels(bot: Bot, update: Update):
    message = update.effective_message
    chats = sql.get_all_channels() or []

    chatlist = ''
    for chat in chats:
        chatlist += "●{} ( <code>{}</code> )\n".format(chat.chat_name, chat.chat_id)


    if len(chats) >= 1:
        text = "List of Channels the bot has been added to:\n\n"+chatlist
    else:
        text = "There are not a member of any Channel"

    if message.reply_to_message:
        message.reply_to_message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        message.reply_text(text, quote=False)




__help__ = """This module does let you add or remove channels and groups manually. It also allows you to list them.

*Admin only:*
 - /listchannels : Will show you a list of all added channels
 - /listchats : Will show you a list of chats your bot is a member of

 - /addchannel <chat id> <channel name> : Adds a channel to your DB (you still need to add the bot manually to the channel)
 - /delchannel <chat id> : Removes a channel from your DB (It will be added again once it recieves data from the channel)

 - /delchat <chat id> : Removes a channel from your DB (It will be added again once it recieves data from the channel)


"""  # no help string

__mod_name__ = "Groups & Channels"

CHATSS_HANDLER = CommandHandler("listchats", chats, filters=CustomFilters.sudo_filter)
ADDCHANNEL_HANDLER = CommandHandler("addchannel", add_channel, filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
LISTCHANNELS_HANDLER = CommandHandler("listchannels", list_channels, filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
DELCHANNEL_HANDLER = CommandHandler("delchannel", del_channel, filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
DELCHAT_HANDLER = CommandHandler("delchat", del_chat, filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

dispatcher.add_handler(CHATSS_HANDLER)
dispatcher.add_handler(ADDCHANNEL_HANDLER)
dispatcher.add_handler(DELCHANNEL_HANDLER)
dispatcher.add_handler(LISTCHANNELS_HANDLER)
dispatcher.add_handler(DELCHAT_HANDLER)