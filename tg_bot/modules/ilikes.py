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


def get_keyboard_locations(chat_id, message_id, found, thanks, notfound):
    img_found = "✅"
    img_thanks = "😍"
    img_notfound = "🚫"
    
    if found >= 100:
        found = "99+"
    if thanks >= 100:
        thanks = "99+"
    if notfound >= 100:
        notfound = "99+"

    tfound = img_found + "   " + str(found)
    tthanks = img_thanks + "   " + str(thanks)
    tnotfound = img_notfound + "   " + str(notfound)

    button_list = [
        InlineKeyboardButton(tfound, callback_data="thanks_key1"),
        InlineKeyboardButton(tthanks, callback_data="thanks_key2"),
        InlineKeyboardButton(tnotfound, callback_data="thanks_key3")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
    return reply_markup


def get_keyboard(chat_id, message_id, up, down):
    img_up = "👍🏻"
    img_down = "👎🏻"
    
    if up >= 100:
        up = "99+"
    if down >= 100:
        down = "99+"

    tup = img_up + "   " + str(up)
    tdown = img_down + "   " + str(down)

    button_list = [
        InlineKeyboardButton(tup, callback_data="thanks_key1"),
        InlineKeyboardButton(tdown, callback_data="thanks_key3")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    return reply_markup



@run_async
def location_handler(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    reply_to_msg = msg.reply_to_message
    try:
        reply_msg_id = msg.reply_to_message.from_user.id
    except Exception as e:
        reply_msg_id = None
        pass

    if Filters.location(msg):
        if ( sql.ilikes_enabled(chat.id) == True ):
            send_like_location_buttons(bot, update, reply_msg_id)

@run_async
def thank_button(bot: Bot, update: Update):
    query = update.callback_query
    user = update.effective_user
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_id = update.effective_message.message_id
    key = query.data
    data = sql.get_iLikes(chat_id, message_id)
    if ( data != False ):
        (found, thanks, notfound, creator, ilikestype) = data

        msg = update.effective_message  # type: Optional[Message]
        reply_to_msg = msg.reply_to_message
        if ( str(ilikestype) == "location"):
            reply = sql.add_iLike_Click(chat_id, message_id, user_id, key, ilikestype)
            bot.answer_callback_query(query.id, text=reply)

            data = sql.get_iLikes(chat_id, message_id)
            if ( data != False ):
                (found, thanks, notfound, creator, ilikestype) = data

            user2 = ""
            if creator:
                sent_user = bot.get_chat(creator)
                if sent_user.username:
                    user2 = " @" + escape_markdown(sent_user.username)
                else:
                    user2 = " [{}](tg://user?id={})".format(sent_user.first_name,
                                                           sent_user.id)

            message_text = "*" + update.effective_message.text + "*"


            keyboard = get_keyboard_locations(chat_id, message_id, found, thanks, notfound)
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        elif ( str(ilikestype) == "question"):
            reply = sql.add_iLike_Click(chat_id, message_id, user_id, key, ilikestype)
            bot.answer_callback_query(query.id, text=reply)

            data = sql.get_iLikes(chat_id, message_id)
            if ( data != False ):
                (up, notused, down, creator, ilikestype) = data


            message_text = "*Die Community dankt*"+str(user2)+"*!*"


            keyboard = get_keyboard(chat_id, message_id, up, down)
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)            
        else:
            reply = sql.add_iLike_Click(chat_id, message_id, user_id, key, ilikestype)
            bot.answer_callback_query(query.id, text=reply)

            data = sql.get_iLikes(chat_id, message_id)
            if ( data != False ):
                (up, notused, down, creator, ilikestype) = data


            user2 = ""
            if creator:
                sent_user = bot.get_chat(creator)
                if sent_user.username:
                    user2 = " @" + escape_markdown(sent_user.username)
                else:
                    user2 = " [{}](tg://user?id={})".format(sent_user.first_name,
                                                           sent_user.id)

            message_text = "*Die Community dankt*"+str(user2)+"*!*"


            keyboard = get_keyboard(chat_id, message_id, up, down)
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    else:
        bot.answer_callback_query(query.id, text="iLike Daten bereits vom Server gelöscht!")



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
        msg = "Automatische iLikes wurde für Standorte aktiviert"
    else:
        msg = "Automatische iLikes wurde für Standorte wieder de-aktiviert"
    send_reply(update, msg, [])


@run_async
def send_like_buttons(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    reply_to_msg = msg.reply_to_message

    if reply_to_msg:
        if Filters.location(reply_to_msg):
            # get user who sent message
            try:
                reply_msg_id = msg.reply_to_message.from_user.id
            except Exception as e:
                reply_msg_id = None
                pass

            user_id = extract_user(msg, args)
            msg_id = msg.message_id
            if user_id:
                send_like_location_buttons(bot, update, reply_msg_id)
            try:
                msg.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("ERROR in ilikes")
        else:
            # get user who sent message
            try:
                reply_msg_id = msg.reply_to_message.from_user.id
            except Exception as e:
                reply_msg_id = None
                pass

            user_id = extract_user(msg, args)
            msg_id = msg.message_id
            if user_id:
                send_like_general_buttons(bot, update, reply_msg_id)
            try:
                msg.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("ERROR in ilikes")
    else:
        if ( args != [] ):

            text = " ".join(args)
            text = "*" + text + "*"
            try:
                reply_msg_id = msg.reply_to_message.from_user.id
            except Exception as e:
                reply_msg_id = None
                pass

            user_id = extract_user(msg, args)
            msg_id = msg.message_id
            if user_id:
                send_like_question_buttons(bot, update, reply_msg_id, text)
            try:
                msg.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("ERROR in ilikes")   
        print(args)
        msg.delete()

@run_async
def send_like_location_buttons(bot: Bot, update: Update, reply_msg_id: None):
    msg = update.effective_message  # type: Optional[Message]

    img_found = "✅"
    img_thanks = "😍"
    img_notfound = "🚫"

    found = "0"
    thanks = "0"
    notfound = "0"

    tfound = img_found + "   " + found
    tthanks = img_thanks + "   " + thanks
    tnotfound = img_notfound + "   " + notfound

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    user2 = ""
    user_id = update.effective_user.id
    if reply_msg_id:
        user_id = msg.reply_to_message.from_user.id

    if user_id:
        sent_user = bot.get_chat(user_id)
        if sent_user.username:
            user2 = " @" + escape_markdown(sent_user.username)
        else:
            user2 = " [{}](tg://user?id={})".format(sent_user.first_name,
                                                   sent_user.id)

    button_list = [
        InlineKeyboardButton(tfound, callback_data="thanks_key1"),
        InlineKeyboardButton(tthanks, callback_data="thanks_key2"),
        InlineKeyboardButton(tnotfound, callback_data="thanks_key3")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))

    text = "*Die Community dankt*"+str(user2)+"*!*"

    sent_message = send(bot, update, text, reply_markup)
    sent_id = sent_message.message_id
    chat_id = chat.id
    sql.add_iLike(chat_id, sent_id, user_id, "location")



@run_async
def send_like_general_buttons(bot: Bot, update: Update, reply_msg_id: None):
    msg = update.effective_message  # type: Optional[Message]

    img_up = "👍🏻"
    img_down = "👎🏻"

    up = "0"
    down = "0"

    tup = img_up + "   " + up
    tdown = img_down + "   " + down

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    user2 = ""
    user_id = update.effective_user.id
    if reply_msg_id:
        user_id = msg.reply_to_message.from_user.id

    if user_id:
        sent_user = bot.get_chat(user_id)
        if sent_user.username:
            user2 = " @" + escape_markdown(sent_user.username)
        else:
            user2 = " [{}](tg://user?id={})".format(sent_user.first_name,
                                                   sent_user.id)

    button_list = [
        InlineKeyboardButton(tup, callback_data="thanks_key1"),
        InlineKeyboardButton(tdown, callback_data="thanks_key3")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

    text = "*Die Community dankt*"+str(user2)+"*!*"

    sent_message = send(bot, update, text, reply_markup)
    sent_id = sent_message.message_id
    chat_id = chat.id
    sql.add_iLike(chat_id, sent_id, user_id, "general")




@run_async
def send_like_question_buttons(bot: Bot, update: Update, text: "No input"):
    msg = update.effective_message  # type: Optional[Message]

    img_up = "👍🏻"
    img_down = "👎🏻"

    up = "0"
    down = "0"

    tup = img_up + "   " + up
    tdown = img_down + "   " + down

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    button_list = [
        InlineKeyboardButton(tup, callback_data="thanks_key1"),
        InlineKeyboardButton(tdown, callback_data="thanks_key3")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

    sent_message = send(bot, update, text, reply_markup)
    sent_id = sent_message.message_id
    chat_id = chat.id
    sql.add_iLike(chat_id, sent_id, user_id, "question")




__help__ = """
This module sends like Buttons

/iLikes : Toggle automatic Location Likes
/ilike  : Send some like Buttons
"""

__mod_name__ = "iLikes"
dispatcher.add_handler(MessageHandler(Filters.location & Filters.group, location_handler), 2)

toggle_handler = CommandHandler("iLikes", toggle_ilikes,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter, pass_args=True)
settings_handler = CommandHandler("ilike", send_like_buttons, pass_args=True)
settings_callback_handler = CallbackQueryHandler(thank_button, pattern=r"thanks_")

dispatcher.add_handler(toggle_handler)
dispatcher.add_handler(settings_handler)
dispatcher.add_handler(settings_callback_handler)

