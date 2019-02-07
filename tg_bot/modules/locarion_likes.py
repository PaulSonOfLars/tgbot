import html
from typing import Optional, List

import telegram.ext as tg
from telegram import Message, Chat, Update, Bot, ParseMode, User, MessageEntity, InlineKeyboardMarkup
from telegram import TelegramError
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters
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

LOCK_TYPES = {'location': Filters.location,
              }


MESSAGES = Filters.location

RESTRICTION_TYPES = {'messages': MESSAGES}

PERM_GROUP = 1
REST_GROUP = 2


class CustomCommandHandler(tg.CommandHandler):
    def __init__(self, command, callback, **kwargs):
        super().__init__(command, callback, **kwargs)

    def check_update(self, update):
        return super().check_update(update) and not (
                sql.is_restr_locked(update.effective_chat.id, 'messages') and not is_user_admin(update.effective_chat,
                                                                                                update.effective_user.id))


tg.CommandHandler = CustomCommandHandler





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
@user_not_admin
def rest_handler(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    if Filters.location(msg):
        print("location found")

    for restriction, filter in RESTRICTION_TYPES.items():
        if filter(msg):
            try:
                pass
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("ERROR in restrictions")
            break



__help__ = """
This module sends Buttons if a Location has been sent to a chat.

"""

__mod_name__ = "Location Likes"
dispatcher.add_handler(MessageHandler(Filters.location & Filters.group, del_lockables), PERM_GROUP)
dispatcher.add_handler(MessageHandler(Filters.location & Filters.group, rest_handler), REST_GROUP)
