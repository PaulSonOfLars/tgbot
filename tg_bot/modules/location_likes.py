import html
from typing import Optional, List

import telegram.ext as tg
from telegram import Message, Chat, Update, Bot, ParseMode, User, MessageEntity, InlineKeyboardMarkup
from telegram import TelegramError
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html

import tg_bot.modules.sql.locks_sql as sql
from tg_bot import dispatcher, SUDO_USERS, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import can_delete, is_user_admin, user_not_admin, user_admin, \
    bot_can_delete, is_bot_admin
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import users_sql
from tg_bot.modules.helper_funcs.extraction import extract_user



# do not async
def send(update, message, keyboard):
    try:
        msg = update.effective_message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    except Exception as e:
        print(e)

    return msg



def send_lock_msg(bot: Bot, update: Update):
    user_id = update.effective_user.id
    if user_id:
        locked_user = bot.get_chat(user_id)
        if locked_user.username:
            user2 = "@" + escape_markdown(locked_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)
        text = "Hey "+user2+",\n_Deine Nachricht hat Medien enthalten die in diesem Chat untersagt sind!_\n*Daher wurde sie gelöscht!*"
    else:
        text = "_Die letzte Nachricht hat Medien enthalten die in diesem Chat untersagt sind!_\n*Daher wurde sie gelöscht!*"

    keyb = []
    keyboard = InlineKeyboardMarkup(keyb)
    sentid = send(update, text, keyboard)  # type: Optional[Message]

    chat = update.effective_chat  # type: Optional[Chat]

    try:
        chat_id = chat.id
        prev_msg = sql.get_lock_msgid(chat_id)

        if prev_msg:
            try:
                bot.delete_message(chat_id, prev_msg)
            except BadRequest as excp:
                pass
        retval = sql.set_lock_msgid(chat_id, sentid.message_id)
    except Exception as e:
        print(e)
        pass


@run_async
def rest_handler(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    if Filters.location(msg):
        print("location found")


@run_async
def settings_button(bot: Bot, update: Update):
    query = update.callback_query
    user = update.effective_user


@run_async
def get_settings(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = msg.text.split(None, 1)


    text = "Click here to get this chat's settings, as well as yours."
    msg.reply_text(text,
                   reply_markup=InlineKeyboardMarkup(
                       [[InlineKeyboardButton(text="Settings",
                                              url="t.me/{}?start=stngs_{}".format(
                                                          bot.username, chat.id))]]))

__help__ = """
This module sends Buttons if a Location has been sent to a chat.

"""

__mod_name__ = "Location Likes"
dispatcher.add_handler(MessageHandler(Filters.location & Filters.group, rest_handler), 2)

settings_handler = CommandHandler("likeit", get_settings)
settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")
dispatcher.add_handler(settings_handler)
dispatcher.add_handler(settings_callback_handler)
