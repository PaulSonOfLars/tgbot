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

import tg_bot.modules.sql.ilikes_sql as sql
from tg_bot import dispatcher, SUDO_USERS, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import can_delete, is_user_admin, user_not_admin, user_admin, \
    bot_can_delete, is_bot_admin
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import users_sql
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters


# do not async
def send(bot: Bot, update: Update, message, keyboard):
    try:
        chat_id = update.effective_chat.id
        msg = bot.send_message(chat_id, message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    except Exception as e:
        print(e)
    return msg



def send_reply(update, message, keyboard):
    try:
        msg = update.effective_message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    except Exception as e:
        print(e)
    return msg


def get_keyboard(chat_id, message_id):
    img_found = "✅"
    img_thanks = "😍"
    img_notfound = "🚫"

    data = sql.get_iLikes(chat_id, message_id)
    (found, thanks, notfound) = data
    
    if found >= 100:
        found = "99+"
    if thanks >= 100:
        thanks = "99+"
    if notfound >= 100:
        notfound = "99+"

    tfound = img_found + " " + str(found)
    tthanks = img_thanks + " " + str(thanks)
    tnotfound = img_notfound + " " + str(notfound)

    button_list = [
        InlineKeyboardButton(tfound, callback_data="thanks_key1"),
        InlineKeyboardButton(tthanks, callback_data="thanks_key2"),
        InlineKeyboardButton(tnotfound, callback_data="thanks_key3")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
    return reply_markup

@run_async
def rest_handler(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    if Filters.location(msg):
        if ( sql.ilikes_enabled(chat.id) == True ):
            get_like_buttons(bot, update)


@run_async
def settings_button(bot: Bot, update: Update):
    query = update.callback_query
    user = update.effective_user
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    message_text = "*" + update.effective_message.text + "*"
    key = query.data

    sql.add_iLike_Click(chat_id, message_id, user_id, key)
    keyboard = get_keyboard(chat_id, message_id)
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

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
@user_admin
def toggle_ilikes(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    retval = sql.toggle_ilikes(chat_id)
    if ( retval == True ):
        msg = "iLikes wurde für Standorte aktiviert"
    else:
        msg = "iLikes wurde für Standorte wieder de-aktiviert"
    send_reply(update, msg, [])


@run_async
def get_like_buttons(bot: Bot, update: Update, args: List[str]):

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)
        img_found = "✅"
        img_thanks = "😍"
        img_notfound = "🚫"

        found = "0"
        thanks = "0"
        notfound = "0"

        tfound = img_found + "  " + found
        tthanks = img_thanks + "  " + thanks
        tnotfound = img_notfound + "  " + notfound

        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        msg = update.effective_message  # type: Optional[Message]


        button_list = [
            InlineKeyboardButton(tfound, callback_data="thanks_key1"),
            InlineKeyboardButton(tthanks, callback_data="thanks_key2"),
            InlineKeyboardButton(tnotfound, callback_data="thanks_key3")
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))

        text = "*Danke für deinen Community-Beitrag!*"

        sent_message = send(bot, update, text, reply_markup)
        sent_id = sent_message.message_id
        chat_id = chat.id
        sql.add_iLike(chat_id, sent_id)


__help__ = """
This module sends Buttons if a Location has been sent to a chat.

"""

__mod_name__ = "Location Likes"
dispatcher.add_handler(MessageHandler(Filters.location & Filters.group, rest_handler), 2)


settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"thanks_")

toggle_handler = CommandHandler("toggle_ilikes", toggle_ilikes,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
settings_handler = CommandHandler("ilike", get_like_buttons, pass_args=True)



dispatcher.add_handler(toggle_handler)
dispatcher.add_handler(settings_handler)
dispatcher.add_handler(settings_callback_handler)

