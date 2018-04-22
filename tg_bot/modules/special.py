from io import BytesIO
from time import sleep
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import is_user_ban_protected

import telegram
import tg_bot.modules.sql.users_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.disable import DisableAbleCommandHandler

USERS_GROUP=4
                                                                                                                                                                                                                                                                               
@run_async                                                                                                                                                                                                                                                                     
def quickscope(bot: Bot, update: Update, args: List[int]):                                                                                                                                                                                                                     
    if args:                                                                                                                                                                                                                                                                   
        chat_id = str(args[1])                                                                                                                                                                                                                                                 
        to_kick = str(args[0])                                                                                                                                                                                                                                                 
    else:                                                                                                                                                                                                                                                                      
        update.effective_message.reply_text("You don't seem to be referring to a chat/user")                                                                                                                                                                                   
    try:                                                                                                                                                                                                                                                                       
        bot.kick_chat_member(chat_id, to_kick)                                                                                                                                                                                                                                 
        update.effective_message.reply_text("Attempted banning " + to_kick + " from" + chat_id)                                                                                                                                                                                
    except BadRequest as excp:                                                                                                                                                                                                                                                 
        update.effective_message.reply_text(excp.message + " " + to_kick)                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                               
@run_async                                                                                                                                                                                                                                                                     
def quickunban(bot: Bot, update: Update, args: List[int]):                                                                                                                                                                                                                     
    if args:                                                                                                                                                                                                                                                                   
        chat_id = str(args[1])                                                                                                                                                                                                                                                 
        to_kick = str(args[0])                                                                                                                                                                                                                                                 
    else:                                                                                                                                                                                                                                                                      
        update.effective_message.reply_text("You don't seem to be referring to a chat/user")                                                                                                                                                                                   
    try:                                                                                                                                                                                                                                                                       
        bot.unban_chat_member(chat_id, to_kick)                                                                                                                                                                                                                                
        update.effective_message.reply_text("Attempted unbanning " + to_kick + " from" + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)

@run_async
def banall(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[0])
        all_mems = sql.get_chat_members(chat_id)
    else:
        chat_id = str(update.effective_chat.id)
        all_mems = sql.get_chat_members(chat_id)
    for mems in all_mems:
        try:
            bot.kick_chat_member(chat_id, mems.user)
            update.effective_message.reply_text("Tried banning " + str(mems.user))
            sleep(0.1)
        except BadRequest as excp:
            update.effective_message.reply_text(excp.message + " " + str(mems.user))
            continue


@run_async
def snipe(bot: Bot, update: Update, args: List[str]):
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        update.effective_message.reply_text("Please give me a chat to echo to!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text("Couldn't send the message. Perhaps I'm not part of that group?")


__help__ = ""  # no help string

__mod_name__ = "Special"

SNIPE_HANDLER = CommandHandler("snipe", snipe, pass_args = True, filters=CustomFilters.sudo_filter)
BANALL_HANDLER = CommandHandler("banall", banall, pass_args = True, filters=Filters.user(OWNER_ID))
QUICKSCOPE_HANDLER = CommandHandler("quickscope", quickscope, pass_args = True, filters=CustomFilters.sudo_filter)
QUICKUNBAN_HANDLER = CommandHandler("quickunban", quickunban, pass_args = True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(BANALL_HANDLER)
dispatcher.add_handler(QUICKSCOPE_HANDLER)
dispatcher.add_handler(QUICKUNBAN_HANDLER)
