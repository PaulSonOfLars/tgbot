import re

import telegram
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, DispatcherHandlerStop, run_async, Filters
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, OWNER_USERNAME
from tg_bot.modules.helper_funcs import user_admin, extract_text, button_markdown_parser
from tg_bot.modules.sql import cust_filters_sql as sql

HANDLER_GROUP = 10
BASIC_FILTER_STRING = "*Filters in this chat:*\n"


@run_async
def list_handlers(bot, update):
    chat = update.effective_chat
    all_handlers = sql.get_chat_filters(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("No filters are active here!")
        return

    filter_list = BASIC_FILTER_STRING
    for handler in all_handlers:
        entry = " - {}\n".format(escape_markdown(handler.keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=telegram.ParseMode.MARKDOWN)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == BASIC_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=telegram.ParseMode.MARKDOWN)


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
def filters(bot, update):
    chat = update.effective_chat
    msg = update.effective_message
    args = msg.text.split(None, 2)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    # set trigger
    keyword = args[1]

    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    buttons = []

    # determine what the contents of the filter are - text, image, sticker, etc
    if len(args) >= 3:
        offset = len(args[2]) - len(msg.text)  # set correct offset relative to command + notename
        content, buttons = button_markdown_parser(args[2], entities=msg.parse_entities(), offset=offset)

    elif msg.reply_to_message and msg.reply_to_message.sticker:
        content = msg.reply_to_message.sticker.file_id
        is_sticker = True

    elif msg.reply_to_message and msg.reply_to_message.document:
        content = msg.reply_to_message.document.file_id
        is_document = True

    elif msg.reply_to_message and msg.reply_to_message.photo:
        content = msg.reply_to_message.photo[-1].file_id  # last elem = best quality
        is_image = True

    elif msg.reply_to_message and msg.reply_to_message.audio:
        content = msg.reply_to_message.audio.file_id
        is_audio = True

    elif msg.reply_to_message and msg.reply_to_message.voice:
        content = msg.reply_to_message.voice.file_id
        is_voice = True

    elif msg.reply_to_message and msg.reply_to_message.video:
        content = msg.reply_to_message.video.file_id
        is_video = True

    else:
        msg.reply_text("You didn't specify what to reply with!")
        return

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    sql.add_filter(chat.id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                   buttons)

    msg.reply_text("Handler {} added!".format(keyword))
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
def stop_filter(bot, update, args):
    chat = update.effective_chat

    if len(args) < 1:
        return

    chat_filters = sql.get_chat_filters(chat.id)

    if not chat_filters:
        update.effective_message.reply_text("No filters are active here!")
        return

    for filt in chat_filters:
        if filt.chat_id == str(chat.id) and filt.keyword == args[0]:
            sql.remove_filter(chat.id, args[0])
            update.effective_message.reply_text("Yep, I'll stop replying to that.")
            raise DispatcherHandlerStop

    update.effective_message.reply_text("That's not a current filter - run /filters for all active filters.")


@run_async
def reply_filter(bot, update):
    chat = update.effective_chat
    message = update.effective_message
    chat_filters = sql.get_chat_filters(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return

    for filt in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(filt.keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            if filt.is_sticker:
                message.reply_sticker(filt.reply)
            elif filt.is_document:
                message.reply_document(filt.reply)
            elif filt.is_image:
                message.reply_photo(filt.reply)
            elif filt.is_audio:
                message.reply_audio(filt.reply)
            elif filt.is_voice:
                message.reply_voice(filt.reply)
            elif filt.is_video:
                message.reply_video(filt.reply)
            elif filt.has_markdown:
                if filt.has_buttons:
                    buttons = sql.get_buttons(chat.id, filt.keyword)
                    keyb = []
                    for btn in buttons:
                        keyb.append([InlineKeyboardButton(btn.name, url=btn.url)])

                    keyboard = InlineKeyboardMarkup(keyb)
                    try:
                        message.reply_text(filt.reply, parse_mode=ParseMode.MARKDOWN,
                                           disable_web_page_preview=True,
                                           reply_markup=keyboard)
                    except BadRequest as e:
                        if e.message == "Unsupported url protocol":
                            message.reply_text("You seem to be trying to use an unsupported url protocol. Telegram "
                                               "doesn't support buttons for some protocols, such as tg://. Please try "
                                               "again, or ask @{} for help.".format(OWNER_USERNAME))
                        else:
                            message.reply_text(
                                "This note is not formatted correctly. Could not send. Contact @{}"
                                " if you can't figure out why!".format(OWNER_USERNAME))
                else:
                    try:
                        message.reply_text(filt.reply, parse_mode=ParseMode.MARKDOWN,
                                           disable_web_page_preview=True)
                    except BadRequest:
                        message.reply_text(
                            "This note is not formatted correctly. Could not send. Contact @{}"
                            " if you can't figure out why!".format(OWNER_USERNAME))

            else:
                message.reply_text(filt.reply)
            break


def __stats__():
    return "{} filters, across {} chats.".format(sql.num_filters(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /filter <keyword> <reply message>: add a filter to this chat. The bot will now reply that message whenever 'keyword' \
 is mentioned. If you reply to a sticker with a keyword, the bot will reply with that sticker.
 - /stop <filter keyword>: stop that filter.
 - /filters: list all active filters in this chat
"""

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter, pass_args=True)
LIST_HANDLER = CommandHandler("filters", list_handlers)
CUST_FILTER_HANDLER = MessageHandler(Filters.text | Filters.command | Filters.sticker | Filters.photo, reply_filter)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
