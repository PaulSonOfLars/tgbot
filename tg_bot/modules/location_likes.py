import html
from typing import Optional, List

import telegram.ext as tg
from telegram import Message, Chat, Update, Bot, ParseMode, User, MessageEntity
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
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
def send(bot: Bot, update: Update, message, keyboard):
    try:
        chat_id = update.effective_chat.id
        #msg = update.effective_message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        msg = bot.send_message(chat_id, message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
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
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    print("button pressed")
    print(query.data)
    print("")
    print(query)
    print("")
    print(user_id)
    print("")
    print(chat_id)
    print("")
    print(message_id)

            # ensure no spinny white circle
    bot.answer_callback_query(query.id)

def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

@run_async
def get_like_buttons(bot: Bot, update: Update):
    img_found = "✅"
    img_thanks = "😍"
    img_notfound = "🚫"

    found = "0"
    thanks = "0"
    notfound = "0"

    tfound = img_found + " " + found
    tthanks = img_thanks + " " + thanks
    tnotfound = img_notfound + " " + notfound

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = msg.text.split(None, 1)

    button_list = [
        InlineKeyboardButton(tfound, callback_data="thanks_key1"),
        InlineKeyboardButton(tthanks, callback_data="thanks_key2"),
        InlineKeyboardButton(tnotfound, callback_data="thanks_key3")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))

    text = "Danke für deinen Beitrag!"

    send(update, text, reply_markup)




__help__ = """
This module sends Buttons if a Location has been sent to a chat.

"""

__mod_name__ = "Location Likes"
dispatcher.add_handler(MessageHandler(Filters.location & Filters.group, rest_handler), 2)

settings_handler = CommandHandler("likeit", get_like_buttons)
settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"thanks_")
dispatcher.add_handler(settings_handler)
dispatcher.add_handler(settings_callback_handler)
